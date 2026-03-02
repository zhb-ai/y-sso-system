"""企业微信 API 客户端

封装 wechatpy 库，提供企业微信通讯录相关 API 调用。
AccessToken 由 wechatpy 内部管理，通过内存 Session 缓存。

使用示例::

    client = WechatWorkClient(
        corp_id="wwxxxxxxxxxx",
        corp_secret="xxxxx",
        callback_token="xxxxx",
        callback_aes_key="xxxxx",
    )
    departments = client.get_departments()
    users = client.get_department_users(1)
"""

from typing import Optional, List, Dict, Any

from wechatpy.enterprise.crypto import WeChatCrypto
from yweb.log import get_logger

logger = get_logger()


# ==================== 内存 Session 存储 ====================


class _MemorySessionStorage:
    """基于内存的 wechatpy session 存储

    用于缓存 AccessToken，避免依赖 Redis。
    wechatpy 内部会在 token 过期时自动刷新。
    """

    def __init__(self):
        self._data: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._data[key] = value

    def delete(self, key: str) -> None:
        self._data.pop(key, None)


# ==================== 企业微信客户端 ====================


class WechatWorkClient:
    """企业微信 API 客户端

    封装 wechatpy 的 WeChatClient，提供通讯录相关操作。
    支持消息回调的签名验证和加解密。

    Attributes:
        corp_id: 企业微信 corp_id
        client: wechatpy 企业微信客户端实例
        crypto: wechatpy 消息加解密实例（可选，用于回调处理）
    """

    def __init__(
        self,
        corp_id: str,
        corp_secret: str,
        callback_token: Optional[str] = None,
        callback_aes_key: Optional[str] = None,
    ):
        """初始化客户端

        Args:
            corp_id: 企业微信企业 ID
            corp_secret: 通讯录同步 Secret
            callback_token: 回调 Token（用于验签和解密）
            callback_aes_key: 回调 EncodingAESKey（用于解密）
        """
        from wechatpy.enterprise import WeChatClient

        self.corp_id = corp_id
        self.client = WeChatClient(
            corp_id,
            corp_secret,
            session=_MemorySessionStorage(),
        )

        # 初始化回调加解密（可选）
        self.crypto = None
        if callback_token and callback_aes_key:
            from wechatpy.enterprise.crypto import WeChatCrypto

            self.crypto = EnterpriseWechatCryptoJson(
                callback_token, callback_aes_key, corp_id
            )

        logger.info(f"企业微信客户端初始化: corp_id={corp_id}")

    # ==================== 部门 API ====================

    def get_departments(self, dept_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取部门列表

        Args:
            dept_id: 父部门 ID，为空时获取全量部门列表

        Returns:
            部门数据列表
        """
        try:
            result = self.client.department.get(id=dept_id)
            logger.debug(f"获取部门列表成功: 共 {len(result)} 个部门")
            return result
        except Exception as e:
            logger.error(f"获取部门列表失败: {e}")
            raise ValueError(f"获取企业微信部门列表失败: {e}")

    def get_department(self, dept_id: int) -> Dict[str, Any]:
        """获取单个部门详情

        Args:
            dept_id: 部门 ID

        Returns:
            部门详情
        """
        try:
            result = self.client.department.get(dept_id)
            return result
        except Exception as e:
            logger.error(f"获取部门详情失败: dept_id={dept_id}, {e}")
            raise ValueError(f"获取企业微信部门详情失败: {e}")

    # ==================== 成员 API ====================

    def get_department_users(self, dept_id: int) -> List[Dict[str, Any]]:
        """获取部门成员详情列表

        Args:
            dept_id: 部门 ID

        Returns:
            成员详情列表
        """
        try:
            result = self.client.department.get_users(
                dept_id, fetch_child=0
            )
            logger.debug(
                f"获取部门成员成功: dept_id={dept_id}, 共 {len(result)} 人"
            )
            return result
        except Exception as e:
            logger.error(f"获取部门成员失败: dept_id={dept_id}, {e}")
            raise ValueError(f"获取企业微信部门成员失败: {e}")

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """获取单个成员详情

        Args:
            user_id: 成员 userid

        Returns:
            成员详情
        """
        try:
            result = self.client.user.get(user_id)
            return result
        except Exception as e:
            logger.error(f"获取成员详情失败: user_id={user_id}, {e}")
            raise ValueError(f"获取企业微信成员详情失败: {e}")
    
    def convert_userid_to_openid(self, user_id: str) -> str:
        """将企业微信 userid 转换为 openid

        Args:
            user_id: 企业微信成员 userid

        Returns:
            转换后的 openid
        """
        try:
            result = self.client.user.convert_to_openid(user_id)
            openid = result.get('openid')
            if not openid:
                raise ValueError("转换失败，未返回 openid")
            logger.debug(f"userid 转 openid 成功: userid={user_id}, openid={openid}")
            return openid
        except Exception as e:
            logger.error(f"userid 转 openid 失败: user_id={user_id}, {e}")
            raise ValueError(f"企业微信 userid 转 openid 失败: {e}")

    # ==================== 回调相关 ====================

    def decrypt_callback_message(
        self,
        msg_signature: str,
        timestamp: str,
        nonce: str,
        msg_encrypt: str,
    ) -> str:
        """解密回调消息

        Args:
            msg_signature: 消息签名
            timestamp: 时间戳
            nonce: 随机数
            msg_encrypt: 加密的消息体

        Returns:
            解密后的 XML 明文

        Raises:
            ValueError: 未配置回调加解密或解密失败
        """
        if not self.crypto:
            raise ValueError("未配置回调 Token 和 EncodingAESKey，无法解密消息")

        try:
            return self.crypto.decrypt_message_json(
                msg_encrypt, msg_signature, timestamp, nonce
            )
        except Exception as e:
            logger.error(f"解密回调消息失败: {e}")
            raise ValueError(f"解密回调消息失败: {e}")

    def verify_callback_url(
        self,
        msg_signature: str,
        timestamp: str,
        nonce: str,
        echostr: str,
    ) -> str:
        """验证回调 URL（企微配置回调时的 GET 验证请求）

        Args:
            msg_signature: 签名
            timestamp: 时间戳
            nonce: 随机数
            echostr: 加密的随机字符串

        Returns:
            解密后的 echostr（需要原样返回给企微）

        Raises:
            ValueError: 未配置回调加解密或验证失败
        """
        if not self.crypto:
            raise ValueError("未配置回调 Token 和 EncodingAESKey，无法验证")

        try:
            return self.crypto.check_signature(
                msg_signature, timestamp, nonce, echostr
            )
        except Exception as e:
            logger.error(f"验证回调 URL 失败: {e}")
            raise ValueError(f"验证回调 URL 失败: {e}")

    # ==================== 工厂方法 ====================

    @classmethod
    def from_organization(cls, org) -> "WechatWorkClient":
        """从 Organization 实体创建客户端

        从 Organization.external_config JSON 中读取配置。

        Args:
            org: Organization 模型实例

        Returns:
            WechatWorkClient 实例

        Raises:
            ValueError: 配置缺失或无效
        """
        if not org.external_corp_id:
            raise ValueError(f"组织 [{org.name}] 未配置企业微信 corp_id")

        config = org.get_external_config_dict()
        wechat_config = config.get("wechat_work", {})

        corp_secret = wechat_config.get("corp_secret")
        if not corp_secret:
            raise ValueError(f"组织 [{org.name}] 未配置企业微信 corp_secret")

        return cls(
            corp_id=org.external_corp_id,
            corp_secret=corp_secret,
            callback_token=wechat_config.get("callback_token"),
            callback_aes_key=wechat_config.get("callback_aes_key"),
        )


class EnterpriseWechatCryptoJson(WeChatCrypto):
    def __init__(self, token, encoding_aes_key, corp_id):
        super().__init__(token, encoding_aes_key, corp_id)
        self.corp_id = corp_id

    def decrypt_message_json(self, msg, signature, timestamp, nonce):
        if isinstance(msg, str):
            encrypt = msg
            from wechatpy.crypto import _get_signature
            from wechatpy.exceptions import InvalidSignatureException
            from wechatpy.crypto import PrpCrypto
            _signature = _get_signature(self.token, timestamp, nonce, encrypt)
            if _signature != signature:

                raise InvalidSignatureException()

            pc = PrpCrypto(self.key)
            return pc.decrypt(encrypt, self._id)
        else:
            return self.decrypt_message(msg, signature, timestamp, nonce)
