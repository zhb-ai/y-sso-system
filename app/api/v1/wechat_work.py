"""企业微信组织架构同步 API

提供企业微信通讯录同步相关的管理接口和回调端点。

接口列表：
    配置管理：
    POST /wechat-work/config/bind       绑定企微配置（管理员）
    POST /wechat-work/config/unbind     解绑企微配置（管理员）
    GET  /wechat-work/config/get        查看绑定状态（管理员）

    同步操作：
    POST /wechat-work/sync/init         初始化全量同步（管理员）
    POST /wechat-work/sync/manual       手动触发同步（管理员）
    GET  /wechat-work/sync/status       查询同步状态（管理员）

    回调端点：
    GET  /wechat-work/webhook/{org_id}  企微回调 URL 验证（公开）
    POST /wechat-work/webhook/{org_id}  接收企微通讯录变更回调（公开，验签）

设计原则（DDD 分层）：
- API 层只负责：参数验证、DTO 转换、异常处理、调用服务层
- 配置管理由 WechatWorkConfigAppService 处理
- 同步逻辑由 WechatWorkSyncService / WebhookHandler 处理
"""

from typing import Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from yweb.response import Resp, OkResponse
from yweb.log import get_logger
from yweb.orm import async_db_call

from app.services.wechat_work_config_app import WechatWorkConfigAppService

logger = get_logger()


# ==================== 请求 Schema ====================


class BindWechatWorkRequest(BaseModel):
    """绑定企业微信配置请求"""
    org_id: int = Field(..., description="组织 ID")
    corp_id: str = Field(..., min_length=1, max_length=255, description="企业微信企业 ID（如 wwxxxxxxxxxx）")
    corp_secret: str = Field(..., min_length=1, description="通讯录同步 Secret")
    callback_token: Optional[str] = Field(None, description="回调 Token（用于接收变更通知）")
    callback_aes_key: Optional[str] = Field(None, description="回调 EncodingAESKey（用于消息解密）")
    login_agent_id: Optional[str] = Field(None, description="自建应用 AgentID（用于扫码登录）")
    login_secret: Optional[str] = Field(None, description="自建应用 Secret（用于扫码登录）")


class UnbindWechatWorkRequest(BaseModel):
    """解绑企业微信配置请求"""
    org_id: int = Field(..., description="组织 ID")


class InitSyncRequest(BaseModel):
    """初始化同步请求"""
    org_id: int = Field(..., description="组织 ID")


class ManualSyncRequest(BaseModel):
    """手动同步请求"""
    org_id: int = Field(..., description="组织 ID")


# ==================== 路由工厂 ====================


def create_wechat_work_router(org_models, management_deps: list = None):
    """创建企业微信同步路由

    Args:
        org_models: OrgModels 实例（setup_organization 的返回值）
        management_deps: 管理接口的依赖列表（如权限检查），
                         仅应用于同步管理接口，不影响 webhook 端点

    Returns:
        APIRouter 实例
    """
    router = APIRouter(prefix="/wechat-work", tags=["企业微信同步"])
    mgmt_deps = management_deps or []

    Organization = org_models.Organization
    config_service = WechatWorkConfigAppService(org_models)

    def _get_wechat_org(org_id: int):
        """获取并验证企微组织"""
        from yweb.organization import ExternalSource

        org = Organization.get(org_id)
        if not org:
            raise ValueError(f"组织不存在: id={org_id}")
        if org.external_source != ExternalSource.WECHAT_WORK.value:
            raise ValueError(
                f"组织 [{org.name}] 不是企业微信同步组织 "
                f"(external_source={org.external_source})"
            )
        return org

    def _build_sync_service(org):
        """构建同步服务实例"""
        from app.domain.wechat_work.client import WechatWorkClient
        from app.domain.wechat_work.sync_service import WechatWorkSyncService

        client = WechatWorkClient.from_organization(org)
        return WechatWorkSyncService(client, org_models)

    def _build_webhook_handler(org):
        """构建回调处理器实例"""
        from app.domain.wechat_work.client import WechatWorkClient
        from app.domain.wechat_work.sync_service import WechatWorkSyncService
        from app.domain.wechat_work.webhook_handler import WebhookHandler

        client = WechatWorkClient.from_organization(org)
        sync_service = WechatWorkSyncService(client, org_models)
        return WebhookHandler(client, sync_service)

    # ==================== 配置管理接口 ====================

    @router.post(
        "/config/bind",
        response_model=OkResponse,
        summary="绑定企业微信",
        description="将组织与企业微信绑定，设置 corp_id、Secret、回调配置等。"
                    "如果组织已绑定，会更新配置。",
        dependencies=mgmt_deps,
    )
    def bind_wechat_work(data: BindWechatWorkRequest):
        """绑定企业微信配置"""
        try:
            result = config_service.bind(
                org_id=data.org_id,
                corp_id=data.corp_id,
                corp_secret=data.corp_secret,
                callback_token=data.callback_token,
                callback_aes_key=data.callback_aes_key,
                login_agent_id=data.login_agent_id,
                login_secret=data.login_secret,
            )
            return Resp.OK(data=result, message="企业微信绑定成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.post(
        "/config/unbind",
        response_model=OkResponse,
        summary="解绑企业微信",
        description="清除组织的企业微信绑定配置。不会删除已同步的部门和员工数据。",
        dependencies=mgmt_deps,
    )
    def unbind_wechat_work(data: UnbindWechatWorkRequest):
        """解绑企业微信配置"""
        try:
            result = config_service.unbind(data.org_id)
            return Resp.OK(data=result, message="企业微信已解绑（已同步的数据保留）")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.get(
        "/config/get",
        response_model=OkResponse,
        summary="查看企微绑定配置",
        description="查看指定组织的企业微信绑定状态和配置信息（Secret 脱敏显示）",
        dependencies=mgmt_deps,
    )
    def get_wechat_work_config(
        org_id: int = Query(..., description="组织 ID"),
    ):
        """查看企微绑定配置"""
        try:
            result = config_service.get_config(org_id)
            return Resp.OK(data=result)
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    # ==================== 同步管理接口 ====================

    @router.post(
        "/sync/init",
        response_model=OkResponse,
        summary="初始化全量同步",
        description="首次从企业微信拉取完整组织架构（部门 + 成员 + 关系），"
                    "同步结果包含新建、更新、删除的数量统计",
        dependencies=mgmt_deps,
    )
    def init_sync(data: InitSyncRequest):
        """初始化全量同步"""
        try:
            org = _get_wechat_org(data.org_id)
            sync_service = _build_sync_service(org)
            result = sync_service.sync_from_external(org.id)
            return Resp.OK(data=result.to_dict(), message="全量同步完成")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.post(
        "/sync/manual",
        response_model=OkResponse,
        summary="手动触发同步",
        description="手动触发与企业微信的组织架构对齐，功能等同于初始化同步",
        dependencies=mgmt_deps,
    )
    def manual_sync(data: ManualSyncRequest):
        """手动触发同步"""
        try:
            org = _get_wechat_org(data.org_id)
            sync_service = _build_sync_service(org)
            result = sync_service.sync_from_external(org.id)
            return Resp.OK(data=result.to_dict(), message="手动同步完成")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.get(
        "/sync/status",
        response_model=OkResponse,
        summary="查询同步状态",
        description="查询指定组织的企业微信同步状态和配置信息",
        dependencies=mgmt_deps,
    )
    def sync_status(
        org_id: int = Query(..., description="组织 ID"),
    ):
        """查询同步状态"""
        try:
            org = _get_wechat_org(org_id)
            config = org.get_external_config_dict()
            wechat_config = config.get("wechat_work", {})

            has_secret = bool(wechat_config.get("corp_secret"))
            has_callback = bool(
                wechat_config.get("callback_token")
                and wechat_config.get("callback_aes_key")
            )

            return Resp.OK(data={
                "org_id": org.id,
                "org_name": org.name,
                "corp_id": org.external_corp_id,
                "external_source": org.external_source,
                "config_status": {
                    "has_corp_secret": has_secret,
                    "has_callback_config": has_callback,
                },
            })
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    # ==================== 企微回调端点（公开，验签保护） ====================

    @router.get(
        "/webhook/{org_id}",
        summary="企微回调 URL 验证",
        description="企业微信配置回调 URL 时发送的 GET 验证请求，"
                    "解密 echostr 并原样返回",
        response_class=PlainTextResponse,
    )
    def verify_webhook(
        org_id: int,
        msg_signature: str = Query(..., description="签名"),
        timestamp: str = Query(..., description="时间戳"),
        nonce: str = Query(..., description="随机数"),
        echostr: str = Query(..., description="加密的随机字符串"),
    ):
        """企微回调 URL 验证（GET 请求）"""
        try:
            from app.domain.wechat_work.client import WechatWorkClient

            org = _get_wechat_org(org_id)
            client = WechatWorkClient.from_organization(org)
            echo = client.verify_callback_url(
                msg_signature, timestamp, nonce, echostr,
            )
            logger.info(f"企微回调 URL 验证成功: org_id={org_id}")
            return PlainTextResponse(content=echo)
        except ValueError as e:
            logger.error(f"企微回调 URL 验证失败: org_id={org_id}, {e}")
            return PlainTextResponse(content="", status_code=403)

    @router.post(
        "/webhook/{org_id}",
        summary="接收企微通讯录变更回调",
        description="接收企业微信推送的通讯录变更事件，自动同步到本地组织架构",
        response_class=PlainTextResponse,
    )
    async def receive_webhook(
        org_id: int,
        request: Request,
        msg_signature: str = Query(..., description="签名"),
        timestamp: str = Query(..., description="时间戳"),
        nonce: str = Query(..., description="随机数"),
    ):
        """接收企微通讯录变更回调（POST 请求）

        始终返回 200 + "success"，避免企微重试加剧并发冲突。
        处理失败时记录错误日志，由定期全量同步兜底数据一致性。
        """
        try:
            body = await request.body()
            body_str = body.decode("utf-8")

            def _handle_callback_sync():
                org = _get_wechat_org(org_id)
                handler = _build_webhook_handler(org)
                handler.handle_callback(
                    org, msg_signature, timestamp, nonce, body_str,
                )

            await async_db_call(_handle_callback_sync)
        except Exception as e:
            logger.error(
                f"处理企微回调异常: org_id={org_id}, {e}", exc_info=True,
            )

        # 无论成功失败，始终返回 success（handler 内部已记录详细日志）
        return PlainTextResponse(content="success")

    return router
