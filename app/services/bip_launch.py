"""BIP 第三方单点登录

门户点击应用编码为 bip 的应用时，由服务端向 BIP 换取一次性 token，
再把登录地址交给浏览器。不参与 OAuth 授权码流程。
服务地址和登录后页面取该应用的第一条重定向 URI。
"""

import base64
import hashlib
import time
from typing import Optional
from urllib.parse import urlparse

import httpx

from yweb.log import get_logger

from app.config import settings

logger = get_logger()

BIP_APP_CODE = "bip"
_TOKEN_TIMEOUT_SECONDS = 30


def generate_security(usercode: str, client_security: str, now_ms: Optional[int] = None) -> str:
    """按 BIP 约定计算 security。

    ts_prefix 取毫秒时间戳前 6 位。
    security = Base64(SHA-256(usercode 字节 + (usercode + client_security + ts_prefix) 字节))
    """
    timestamp = int(time.time() * 1000) if now_ms is None else now_ms
    ts_prefix = str(timestamp)[:6]
    key = usercode + client_security + ts_prefix

    digest = hashlib.sha256()
    digest.update(usercode.encode("utf-8"))
    digest.update(key.encode("utf-8"))
    return base64.b64encode(digest.digest()).decode("utf-8")


def build_login_url(base_url: str, token: str, redirect_uri: str) -> str:
    """拼接 BIP 第三方登录地址。"""
    login_page = (
        f"{base_url.rstrip('/')}/nccloud/resources/uap/rbac/thirdpartylogin/main/index.html"
    )
    return f"{login_page}?accesstoken={token}&redirect_uri={redirect_uri}"


def _is_token(text: str) -> bool:
    if not text:
        return False
    if text.startswith("<") or text.startswith("{"):
        return False
    lowered = text.lower()
    if any(word in lowered for word in ("error", "exception", "找不到", "未找到", "失败")):
        return False
    return len(text) >= 8


def resolve_bip_address(redirect_uris) -> tuple[str, str]:
    """从应用重定向地址得到 BIP 服务根地址和登录后页面。

    使用第一条非空地址。服务根地址只保留协议、主机和端口。
    """
    redirect_uri = ""
    for raw in redirect_uris or []:
        text = str(raw or "").strip()
        if text:
            redirect_uri = text
            break
    if not redirect_uri:
        raise ValueError(
            "无法登录 BIP。应用没有重定向地址。请在应用管理填写 BIP 首页，例如 http://主机/nccloud。"
        )

    parsed = urlparse(redirect_uri)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
        raise ValueError(
            "无法登录 BIP。重定向地址缺少协议或主机。请填写完整地址，例如 http://主机/nccloud。"
        )
    base_url = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return base_url, redirect_uri


def _require_config() -> dict:
    bip = settings.bip
    client_id = (bip.client_id or "").strip()
    client_secret = bip.client_secret or ""
    dsname = (bip.dsname or "").strip()
    if not client_id or not client_secret or not dsname:
        raise ValueError("BIP 连接信息未配置完整")

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "dsname": dsname,
        "busi_center_code": (bip.busi_center_code or "").strip(),
        "lang_code": (bip.lang_code or "").strip(),
        "auth_type": (bip.auth_type or "default").strip() or "default",
    }


def request_access_token(usercode: str, config: dict) -> str:
    """向 BIP 申请一次性 access token。失败时抛出 ValueError。"""
    security = generate_security(usercode, config["client_secret"])
    params = {
        "type": config["auth_type"],
        "dsname": config["dsname"],
        "usercode": usercode,
        "client_id": config["client_id"],
        "security": security,
    }
    if config["busi_center_code"]:
        params["busicentercode"] = config["busi_center_code"]
    if config["lang_code"]:
        params["langcode"] = config["lang_code"]

    body = "&".join(f"{key}={value}" for key, value in params.items())
    body = body.replace("+", "%2B")
    url = f"{config['base_url']}/service/genThirdPartyAccessToken"

    try:
        response = httpx.post(
            url,
            content=body.encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=_TOKEN_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        logger.warning("BIP 令牌请求失败 usercode=%s error=%s", usercode, exc)
        raise ValueError("无法连接 BIP 服务器") from exc

    token = response.text.strip()
    logger.info("BIP 令牌请求完成 usercode=%s status=%s", usercode, response.status_code)
    if response.status_code == 401:
        raise ValueError("BIP 拒绝签发登录令牌")
    if response.status_code != 200 or not _is_token(token):
        raise ValueError("BIP 未返回有效登录令牌")
    return token


class BipLaunchService:
    """为当前登录用户生成 BIP 登录地址。"""

    def __init__(self, application_model):
        self.application_model = application_model

    def launch(self, user) -> str:
        application = self.application_model.query.filter_by(
            code=BIP_APP_CODE,
            is_active=True,
        ).first()
        if application is None:
            raise ValueError("BIP 应用不存在或已停用")

        usercode = getattr(user, "username", None)
        if isinstance(usercode, str):
            usercode = usercode.strip()
        if not usercode:
            raise ValueError("当前用户没有登录名，无法登录 BIP")

        config = _require_config()
        base_url, redirect_uri = resolve_bip_address(application.get_redirect_uris())
        config["base_url"] = base_url
        config["redirect_uri"] = redirect_uri
        token = request_access_token(usercode, config)
        return build_login_url(base_url, token, redirect_uri)
