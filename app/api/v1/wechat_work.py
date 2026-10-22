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
    POST /wechat-work/callback          接收明文回调并同步成员（公开）
    POST /wechat-work/callback/{org_id} 接收明文回调并同步成员（公开）

设计原则（DDD 分层）：
- API 层只负责：参数验证、DTO 转换、异常处理、调用服务层
- 配置管理由 WechatWorkConfigAppService 处理
- 同步逻辑由 WechatWorkSyncService / WebhookHandler 处理
"""

import json
import xml.etree.ElementTree as ET
from typing import Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from yweb import DTO
from yweb.response import ItemResponse, OkResponse, Resp
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


class CallbackSyncUserResponse(DTO):
    """明文回调同步一名成员的结果"""
    org_id: int = Field(0, description="组织 ID")
    userid: str = Field("", description="企业微信 userid")
    employee_id: int = Field(0, description="员工 ID")
    employee_name: str = Field("", description="员工姓名")
    is_new_employee: bool = Field(False, description="本次是否新建员工")
    user_id: int = Field(0, description="关联的系统用户 ID")
    username: str = Field("", description="系统用户名")
    account_created: bool = Field(False, description="本次是否新建系统用户")


def _first_text(*values) -> str:
    """返回第一个非空白文本。"""
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


_USERID_KEYS = ("UserID", "userid", "user_id", "UserId")
_USERID_FALLBACK_KEYS = ("id",)
_CORP_ID_KEYS = ("ToUserName", "corp_id", "CorpID")
_NESTED_KEYS = ("data", "event")


def _xml_node_to_data(element):
    """把 XML 节点转成字符串或字典。子节点保留为嵌套字典。"""
    children = list(element)
    if not children:
        return (element.text or "").strip()
    data = {}
    for child in children:
        value = _xml_node_to_data(child)
        current = data.get(child.tag)
        if current is None:
            data[child.tag] = value
        elif isinstance(current, list):
            current.append(value)
        else:
            data[child.tag] = [current, value]
    return data


def _parse_callback_payload(raw_text: str, content_type: str) -> dict:
    """解析明文回调正文。支持企微 XML 和 JSON，保留一层嵌套对象。"""
    text = (raw_text or "").lstrip("\ufeff").strip()
    if not text:
        return {}
    content = (content_type or "").lower()
    looks_xml = text.startswith("<")
    looks_json = text.startswith("{") or text.startswith("[")
    if looks_xml or ("xml" in content and not looks_json):
        try:
            root = ET.fromstring(text)
        except ET.ParseError as exc:
            raise ValueError(f"回调 XML 解析失败: {exc}") from exc
        parsed = _xml_node_to_data(root)
        if not isinstance(parsed, dict):
            return {}
        return parsed
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"回调 JSON 解析失败: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("回调 JSON 必须是对象")
    return payload


def _mapping_text(mapping, keys) -> str:
    """按给定字段顺序读取第一个非空文本。"""
    if not isinstance(mapping, dict):
        return ""
    for key in keys:
        text = _first_text(mapping.get(key))
        if text:
            return text
    return ""


def _payload_sources(payload: dict) -> list:
    """正文顶层，以及 data / event 嵌套对象。"""
    sources = [payload]
    for key in _NESTED_KEYS:
        nested = payload.get(key)
        if isinstance(nested, dict):
            sources.append(nested)
    return sources


def _extract_by_key_order(payload: dict, query: dict, keys) -> str:
    """按字段顺序读取。每个字段先看正文顶层和 data/event，全部字段之后再看 query。"""
    for key in keys:
        for source in _payload_sources(payload):
            found = _mapping_text(source, (key,))
            if found:
                return found
    return _mapping_text(query, keys)


def _extract_userid(payload: dict, query: dict) -> str:
    """读取成员 userid。

    显式字段优先于通用 id，避免事件 id 盖住 data.userid。
    顺序：UserID、userid、user_id、UserId，然后 id。
    """
    found = _extract_by_key_order(payload, query, _USERID_KEYS)
    if found:
        return found
    return _extract_by_key_order(payload, query, _USERID_FALLBACK_KEYS)


def _extract_corp_id(payload: dict, query: dict) -> str:
    """读取 corp_id。正文 ToUserName、corp_id、CorpID 优先于 query。"""
    return _extract_by_key_order(payload, query, _CORP_ID_KEYS)


def _parse_org_id_text(raw, field_name: str = "org_id"):
    """把 org_id 转成整数。空值返回 None。"""
    text = _first_text(raw)
    if not text:
        return None
    try:
        return int(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} 不是有效整数: {text}") from exc


def _org_id_from_callback(path_org_id, query: dict, payload: dict):
    """按路径、query、正文的顺序读取 org_id。"""
    if path_org_id is not None:
        return int(path_org_id)
    query_org_id = _parse_org_id_text(
        _first_text(query.get("org_id"), query.get("OrgId")) or None
    )
    if query_org_id is not None:
        return query_org_id
    for source in _payload_sources(payload):
        body_org_id = _parse_org_id_text(
            _first_text(source.get("org_id"), source.get("OrgId")) or None
        )
        if body_org_id is not None:
            return body_org_id
    return None


# ==================== 路由工厂 ====================


def create_wechat_work_router(org_models, management_deps: list = None):
    """创建企业微信同步路由

    Args:
        org_models: OrgModels 实例（setup_organization 的返回值）
        management_deps: 管理接口的依赖列表（如权限检查），
                         仅应用于同步管理接口，不影响 webhook 与明文回调端点

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

    def _sync_http_response(result, success_message: str):
        """将同步结果转成前端可展示的 HTTP 响应

        部分失败时使用 Warning，把错误明细放到 msg_details，
        避免页面只看到“同步完成”而丢失定位信息。
        """
        payload = result.to_dict()
        errors = payload.get("errors") or []
        if errors:
            return Resp.Warning(
                message="同步完成，但有失败",
                data=payload,
                msg_details=errors,
            )
        return Resp.OK(data=payload, message=success_message)

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
            return _sync_http_response(result, "全量同步完成")
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
            return _sync_http_response(result, "手动同步完成")
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

    # ==================== 明文回调转发（公开，无 JWT） ====================

    async def _receive_plaintext_callback(
        request: Request,
        path_org_id: Optional[int],
    ):
        """解析明文回调，定位组织，并同步该成员。"""
        raw_bytes = await request.body()
        raw_text = raw_bytes.decode("utf-8", errors="replace")
        content_type = request.headers.get("content-type", "")
        query = dict(request.query_params)
        logger.info(
            f"收到企微转发回调请求: path={request.url.path}, "
            f"query={query}, content_type={content_type}, raw_body={raw_text}"
        )
        try:
            parsed = _parse_callback_payload(raw_text, content_type)
            logger.info(f"企微转发回调解析结果: parsed_data={parsed}")
            userid = _extract_userid(parsed, query)
            corp_id = _extract_corp_id(parsed, query)
            org_id_value = _org_id_from_callback(path_org_id, query, parsed)
            logger.info(
                f"企微转发回调解析字段: userid={userid}, "
                f"org_id={org_id_value}, corp_id={corp_id}"
            )
            if not userid:
                return Resp.BadRequest(message="缺少 userid 参数")

            def _sync_member():
                org = _resolve_callback_org(org_id_value, corp_id)
                result = _build_sync_service(org).sync_user_by_userid(org, userid)
                return org, result

            org, result = await async_db_call(_sync_member)
            employee = result["employee"]
            account_created = bool(result["account_created"])
            message = (
                "成员同步并创建用户成功"
                if account_created
                else "成员同步成功（用户账号已存在）"
            )
            logger.info(
                f"明文回调同步成员完成: org_id={org.id}, userid={userid}, "
                f"employee_id={employee.id}, account_created={account_created}"
            )
            return Resp.OK(
                data=CallbackSyncUserResponse(
                    org_id=org.id,
                    userid=userid,
                    employee_id=employee.id,
                    employee_name=employee.name or "",
                    is_new_employee=bool(result["is_new_employee"]),
                    user_id=int(result["user_id"]),
                    username=str(result["username"] or ""),
                    account_created=account_created,
                ),
                message=message,
            )
        except ValueError as exc:
            logger.warning(f"明文回调同步被拒绝: {exc}")
            return Resp.BadRequest(message=str(exc))

    def _resolve_callback_org(org_id_value, corp_id: str):
        """按 org_id、corp_id，或唯一的企微组织定位同步目标。"""
        from yweb.organization import ExternalSource

        if org_id_value is not None:
            return _get_wechat_org(org_id_value)
        if corp_id:
            orgs = Organization.query.filter(
                Organization.external_source == ExternalSource.WECHAT_WORK.value,
                Organization.external_corp_id == corp_id,
            ).all()
            if len(orgs) == 1:
                return orgs[0]
            if not orgs:
                raise ValueError(f"未找到 corp_id={corp_id} 对应的企业微信组织")
            raise ValueError(
                f"corp_id={corp_id} 匹配到多个企业微信组织。请在请求中提供 org_id。"
            )

        orgs = Organization.query.filter(
            Organization.external_source == ExternalSource.WECHAT_WORK.value,
        ).all()
        if len(orgs) == 1:
            return orgs[0]
        if len(orgs) == 0:
            raise ValueError("未找到已绑定企业微信的组织")
        raise ValueError("存在多个已绑定企业微信的组织，请提供 org_id 或 corp_id")

    callback_summary = "接收明文回调并同步成员"
    callback_description = (
        "接收外部系统转发的企业微信明文回调。正文可以是解密后的 XML，也可以是 JSON。"
        "userid 从 UserID、userid、user_id、UserId、id，或 data/event 嵌套字段，或 query 读取。"
        "org_id 优先级为路径、query、正文。corp_id 优先级为正文 ToUserName、corp_id、CorpID，然后是 query。"
        "按 userid 拉取成员，写入员工、部门和系统用户。此接口不校验 JWT。"
    )

    @router.post(
        "/callback",
        response_model=ItemResponse[CallbackSyncUserResponse],
        summary=callback_summary,
        description=callback_description,
    )
    async def receive_plaintext_callback(request: Request):
        """接收不带路径组织 ID 的明文回调。"""
        return await _receive_plaintext_callback(request, None)

    @router.post(
        "/callback/{org_id}",
        response_model=ItemResponse[CallbackSyncUserResponse],
        summary=callback_summary,
        description=callback_description + "路径中的 org_id 优先于 query 和正文。",
    )
    async def receive_plaintext_callback_for_org(org_id: int, request: Request):
        """接收带路径组织 ID 的明文回调。"""
        return await _receive_plaintext_callback(request, org_id)

    return router
