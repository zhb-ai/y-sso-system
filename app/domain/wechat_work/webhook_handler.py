"""企业微信通讯录变更回调处理器

解析企微推送的通讯录变更事件，分发到 WechatWorkSyncService 对应的处理方法。

企微回调流程：
1. 企微 POST 加密的 XML 消息到回调 URL
2. 本模块解密并解析 XML
3. 根据事件类型（ChangeType）分发处理

支持的事件类型：
- create_party / update_party / delete_party（部门）
- create_user / update_user / delete_user（成员）
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional

from yweb.log import get_logger

from .client import WechatWorkClient
from .sync_service import WechatWorkSyncService

logger = get_logger()


class WebhookHandler:
    """企业微信通讯录变更回调处理器

    Attributes:
        client: 企业微信 API 客户端（用于解密消息）
        sync_service: 同步服务（用于处理具体事件）
    """

    # 事件分发映射表
    EVENT_HANDLERS = {
        "create_party": "handle_create_department",
        "update_party": "handle_update_department",
        "delete_party": "handle_delete_department",
        "create_user": "handle_create_user",
        "update_user": "handle_update_user",
        "delete_user": "handle_delete_user",
    }

    def __init__(
        self,
        client: WechatWorkClient,
        sync_service: WechatWorkSyncService,
    ):
        self.client = client
        self.sync_service = sync_service

    def handle_callback(
        self,
        org,
        msg_signature: str,
        timestamp: str,
        nonce: str,
        request_body: str,
    ) -> str:
        """处理企微回调请求

        始终返回 "success"，避免企微重试加剧并发冲突。
        处理失败时记录错误日志，由定期全量同步兜底数据一致性。

        Args:
            org: Organization 实例
            msg_signature: 消息签名（URL 参数）
            timestamp: 时间戳（URL 参数）
            nonce: 随机数（URL 参数）
            request_body: 请求体（XML 格式的加密消息）

        Returns:
            始终返回 "success"
        """
        try:
            # 1. 从请求体中提取加密消息
            encrypt_msg = self._extract_encrypt_from_xml(request_body)
            if not encrypt_msg:
                logger.error("回调消息体中未找到 Encrypt 字段")
                return "success"

            # 2. 解密消息
            decrypted_xml = self.client.decrypt_callback_message(
                msg_signature, timestamp, nonce, encrypt_msg
            )

            # 3. 解析事件
            event_data = self._parse_event_xml(decrypted_xml)
            if not event_data:
                logger.warning("解析回调事件失败")
                return "success"

            # 4. 分发处理
            return self._dispatch_event(org, event_data)

        except Exception as e:
            logger.error(f"处理回调消息异常: {e}", exc_info=True)
            return "success"

    def _dispatch_event(self, org, event_data: Dict[str, Any]) -> str:
        """根据事件类型分发到对应处理方法

        始终返回 "success"，即使处理失败也不触发企微重试。
        重试只会加剧锁竞争，由定期全量同步兜底。

        Args:
            org: Organization 实例
            event_data: 解析后的事件数据

        Returns:
            始终返回 "success"
        """
        event_type = event_data.get("Event", "")
        change_type = event_data.get("ChangeType", "")

        # 只处理通讯录变更事件
        if event_type != "change_contact":
            logger.debug(f"忽略非通讯录变更事件: Event={event_type}")
            return "success"

        handler_name = self.EVENT_HANDLERS.get(change_type)
        if not handler_name:
            logger.debug(f"忽略不支持的变更类型: ChangeType={change_type}")
            return "success"

        handler = getattr(self.sync_service, handler_name, None)
        if not handler:
            logger.error(f"同步服务缺少处理方法: {handler_name}")
            return "success"

        try:
            # 使用同步锁保护增量操作（超时延长到 60s）
            lock = WechatWorkSyncService._get_lock(org.id)
            if not lock.acquire(blocking=True, timeout=60):
                logger.warning(
                    f"获取同步锁超时（60s），跳过事件但返回 success: "
                    f"ChangeType={change_type}"
                )
                return "success"

            try:
                handler(org, event_data)
            finally:
                lock.release()

            logger.info(
                f"回调事件处理成功: Event={event_type}, "
                f"ChangeType={change_type}"
            )
            return "success"

        except Exception as e:
            logger.error(
                f"回调事件处理失败: ChangeType={change_type}, error={e}",
                exc_info=True,
            )
            return "success"

    @staticmethod
    def _extract_encrypt_from_xml(xml_str: str) -> Optional[str]:
        """从 XML 请求体中提取 Encrypt 字段

        企微回调的请求体格式::

            <xml>
                <ToUserName><![CDATA[corp_id]]></ToUserName>
                <AgentID><![CDATA[xxx]]></AgentID>
                <Encrypt><![CDATA[encrypted_msg]]></Encrypt>
            </xml>
        """
        try:
            root = ET.fromstring(xml_str)
            encrypt_node = root.find("Encrypt")
            if encrypt_node is not None and encrypt_node.text:
                return encrypt_node.text
            return None
        except ET.ParseError as e:
            logger.error(f"解析回调 XML 失败: {e}")
            return None

    @staticmethod
    def _parse_event_xml(xml_str: str) -> Optional[Dict[str, Any]]:
        """解析解密后的事件 XML 为字典

        解密后的通讯录变更事件格式示例::

            <xml>
                <ToUserName><![CDATA[corp_id]]></ToUserName>
                <FromUserName><![CDATA[sys]]></FromUserName>
                <CreateTime>1234567890</CreateTime>
                <MsgType><![CDATA[event]]></MsgType>
                <Event><![CDATA[change_contact]]></Event>
                <ChangeType><![CDATA[create_user]]></ChangeType>
                <UserID><![CDATA[zhangsan]]></UserID>
                <Name><![CDATA[张三]]></Name>
                ...
            </xml>
        """
        try:
            root = ET.fromstring(xml_str)
            data = {}
            for child in root:
                data[child.tag] = child.text or ""
            return data
        except ET.ParseError as e:
            logger.error(f"解析事件 XML 失败: {e}")
            return None
