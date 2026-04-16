"""OAuth2 授权服务器 API

本模块实现 SSO 作为 OAuth2 Provider 的核心端点，使用动词风格路由。
所有端点统一前缀 /api/v1/oauth2/，按认证要求分为公开端点和受保护端点。

端点清单：
    GET  /api/v1/oauth2/authorize   → 授权入口（公开，校验参数后引导登录/授权）
    POST /api/v1/oauth2/authorize   → 用户授权确认（需 JWT，生成授权码并重定向）
    POST /api/v1/oauth2/token       → 令牌端点（公开，客户端凭证认证）
    GET  /api/v1/oauth2/userinfo    → 用户信息端点（Bearer Token 认证）

OAuth2 Authorization Code 流程：
    1. 外部应用 → GET /authorize?client_id=&redirect_uri=&response_type=code&state=
    2. SSO 校验参数 → 未登录则重定向到前端登录页，已登录则自动授权
    3. 登录/授权后 → POST /authorize 生成授权码，重定向回 redirect_uri?code=&state=
    4. 外部应用 → POST /token (grant_type=authorization_code) 换取 access_token
    5. 外部应用 → GET /userinfo 获取用户信息
"""

from ipaddress import ip_address, ip_network
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Query, Form, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from yweb.log import get_logger

from app.config import settings
from app.services.oauth2_security import (
    build_jwks,
    is_rs256_enabled,
    get_runtime_jwt_public_key,
    get_oidc_issuer,
    build_oidc_url,
)

logger = get_logger()


# ==================== DTO 定义 ====================


class AuthorizeConfirmRequest(BaseModel):
    """授权确认请求（前端 POST）"""
    client_id: str
    redirect_uri: str
    scope: Optional[str] = None
    state: Optional[str] = None
    nonce: Optional[str] = None
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None


def _get_settings_value(config, key: str, default=None):
    """兼容 dict / 对象两种配置读取方式"""
    if config is None:
        return default
    if isinstance(config, dict):
        return config.get(key, default)
    return getattr(config, key, default)


def _is_trusted_proxy(remote_ip: Optional[str], trusted_proxies) -> bool:
    """判断当前连接来源是否为受信任代理"""
    if not remote_ip:
        return False

    try:
        remote_addr = ip_address(remote_ip)
    except ValueError:
        return False

    for item in trusted_proxies or []:
        candidate = str(item or "").strip()
        if not candidate:
            continue
        try:
            if "/" in candidate:
                if remote_addr in ip_network(candidate, strict=False):
                    return True
            elif remote_addr == ip_address(candidate):
                return True
        except ValueError:
            continue
    return False


def _get_request_client_ip(request: Request) -> Optional[str]:
    """提取请求真实来源 IP"""
    remote_ip = request.client.host if request.client else None
    ip_access_config = getattr(settings, "ip_access", None)
    trusted_proxies = _get_settings_value(ip_access_config, "trusted_proxies", []) or []

    if _is_trusted_proxy(remote_ip, trusted_proxies):
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            real_ip = forwarded_for.split(",")[0].strip()
            if real_ip:
                return real_ip

        real_ip = request.headers.get("X-Real-IP", "").strip()
        if real_ip:
            return real_ip

    return remote_ip


def _is_ip_whitelist_error(error_msg: str) -> bool:
    """判断是否为 IP 白名单拒绝"""
    return "白名单" in error_msg or "来源IP" in error_msg


# ==================== 路由工厂 ====================


def create_oauth2_provider_router(
    oauth2_provider_service,
    get_current_user,
    get_current_user_optional,
    frontend_login_url: str = "/sso/login",
) -> APIRouter:
    """创建 OAuth2 Provider 路由

    Args:
        oauth2_provider_service: OAuth2ProviderService 实例
        get_current_user: JWT 必须认证依赖（未登录抛 401）
        get_current_user_optional: JWT 可选认证依赖（未登录返回 None）
        frontend_login_url: 前端 SSO 登录页路径

    Returns:
        APIRouter
    """
    router = APIRouter(prefix="/oauth2", tags=["OAuth2 授权服务器"])
    basic_auth = HTTPBasic(auto_error=False)

    # ------------------------------------------------------------------
    # GET /authorize — 授权入口（公开）
    # ------------------------------------------------------------------
    @router.get(
        "/authorize",
        summary="OAuth2 授权入口",
        description=(
            "外部应用将用户重定向到此端点。"
            "如果用户已登录（携带有效 JWT Cookie），自动生成授权码并重定向回客户端；"
            "否则重定向到前端 SSO 登录页。"
        ),
    )
    def authorize(
        request: Request,
        response_type: str = Query(..., description="响应类型，必须为 code"),
        client_id: str = Query(..., description="客户端 ID"),
        redirect_uri: str = Query(..., description="回调地址"),
        scope: str = Query(None, description="授权范围"),
        state: str = Query(None, description="CSRF state 参数"),
        nonce: str = Query(None, description="OIDC nonce 参数"),
        code_challenge: str = Query(None, description="PKCE code_challenge"),
        code_challenge_method: str = Query(None, description="PKCE code_challenge_method"),
        current_user=Depends(get_current_user_optional),
    ):
        # 1. 验证客户端和参数
        try:
            app = oauth2_provider_service.validate_authorize_request(
                client_id=client_id,
                redirect_uri=redirect_uri,
                response_type=response_type,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
            )
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid_request",
                    "error_description": str(e),
                },
            )

        # 2. 用户已登录 → 自动授权，生成授权码并重定向
        if current_user:
            try:
                auth_code = oauth2_provider_service.create_authorization_code(
                    application_id=app.id,
                    user_id=current_user.id,
                    redirect_uri=redirect_uri,
                    scope=scope,
                    state=state,
                    nonce=nonce,
                    code_challenge=code_challenge,
                    code_challenge_method=code_challenge_method,
                )
                params = {"code": auth_code.code}
                if state:
                    params["state"] = state
                return RedirectResponse(
                    f"{redirect_uri}?{urlencode(params)}",
                    status_code=302,
                )
            except ValueError as e:
                error_params = urlencode({
                    "error": "server_error",
                    "error_description": str(e),
                    "state": state or "",
                })
                return RedirectResponse(
                    f"{redirect_uri}?{error_params}",
                    status_code=302,
                )

        # 3. 用户未登录 → 重定向到前端 SSO 登录页
        login_params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": response_type,
        }
        if scope:
            login_params["scope"] = scope
        if state:
            login_params["state"] = state
        if nonce:
            login_params["nonce"] = nonce
        if code_challenge:
            login_params["code_challenge"] = code_challenge
        if code_challenge_method:
            login_params["code_challenge_method"] = code_challenge_method

        frontend_url = f"{frontend_login_url}?{urlencode(login_params)}"
        return RedirectResponse(frontend_url, status_code=302)

    # ------------------------------------------------------------------
    # POST /authorize — 用户授权确认（需 JWT）
    # ------------------------------------------------------------------
    @router.post(
        "/authorize",
        summary="用户授权确认",
        description=(
            "前端 SSO 登录页在用户登录成功后调用此端点，"
            "生成授权码并返回重定向 URL。"
        ),
    )
    def authorize_confirm(
        data: AuthorizeConfirmRequest,
        current_user=Depends(get_current_user),
    ):
        # 1. 验证客户端和参数
        try:
            app = oauth2_provider_service.validate_authorize_request(
                client_id=data.client_id,
                redirect_uri=data.redirect_uri,
                code_challenge=data.code_challenge,
                code_challenge_method=data.code_challenge_method,
            )
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid_request",
                    "error_description": str(e),
                },
            )

        # 2. 生成授权码
        try:
            auth_code = oauth2_provider_service.create_authorization_code(
                application_id=app.id,
                user_id=current_user.id,
                redirect_uri=data.redirect_uri,
                scope=data.scope,
                state=data.state,
                nonce=data.nonce,
                code_challenge=data.code_challenge,
                code_challenge_method=data.code_challenge_method,
            )
        except ValueError as e:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "server_error",
                    "error_description": str(e),
                },
            )

        # 3. 构造重定向 URL
        params = {"code": auth_code.code}
        if data.state:
            params["state"] = data.state

        redirect_url = f"{data.redirect_uri}?{urlencode(params)}"

        return {
            "redirect_url": redirect_url,
            "code": auth_code.code,
        }

    # ------------------------------------------------------------------
    # POST /token — 令牌端点（公开，客户端凭证认证）
    # ------------------------------------------------------------------
    @router.post(
        "/token",
        summary="OAuth2 令牌端点",
        description=(
            "支持两种 grant_type：\n"
            "- authorization_code: 用授权码换取 access_token\n"
            "- refresh_token: 刷新 access_token\n\n"
            "客户端认证支持 HTTP Basic Auth 和表单参数两种方式。"
        ),
    )
    def token(
        request: Request,
        grant_type: str = Form(..., description="授权类型"),
        code: str = Form(None, description="授权码（authorization_code 时必填）"),
        redirect_uri: str = Form(None, description="重定向URI（authorization_code 时必填）"),
        client_id: str = Form(None, description="客户端ID"),
        client_secret: str = Form(None, description="客户端密钥"),
        code_verifier: str = Form(None, description="PKCE code_verifier"),
        refresh_token: str = Form(None, description="刷新令牌（refresh_token 时必填）"),
        credentials: HTTPBasicCredentials = Depends(basic_auth),
    ):
        source_ip = _get_request_client_ip(request)

        # 优先使用 HTTP Basic Auth
        if credentials and credentials.username:
            client_id = credentials.username
            client_secret = credentials.password

        if not client_id:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "invalid_client",
                    "error_description": "缺少客户端ID",
                },
            )

        try:
            if grant_type == "authorization_code":
                if not code or not redirect_uri:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "invalid_request",
                            "error_description": "authorization_code 需要 code 和 redirect_uri 参数",
                        },
                    )
                result = oauth2_provider_service.exchange_code_for_token(
                    code=code,
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=redirect_uri,
                    code_verifier=code_verifier,
                    source_ip=source_ip,
                )
                return result

            elif grant_type == "refresh_token":
                if not refresh_token:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "invalid_request",
                            "error_description": "refresh_token 需要 refresh_token 参数",
                        },
                    )
                result = oauth2_provider_service.refresh_access_token(
                    refresh_token=refresh_token,
                    client_id=client_id,
                    client_secret=client_secret,
                    source_ip=source_ip,
                )
                return result

            else:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "unsupported_grant_type",
                        "error_description": f"不支持的授权类型: {grant_type}",
                    },
                )

        except ValueError as e:
            error_msg = str(e)
            # 区分错误类型
            if "客户端" in error_msg or "密钥" in error_msg or _is_ip_whitelist_error(error_msg):
                return JSONResponse(
                    status_code=401,
                    content={"error": "invalid_client", "error_description": error_msg},
                )
            else:
                return JSONResponse(
                    status_code=400,
                    content={"error": "invalid_grant", "error_description": error_msg},
                )

    # ------------------------------------------------------------------
    # GET /userinfo — 用户信息端点（Bearer Token 认证）
    # ------------------------------------------------------------------
    @router.get(
        "/userinfo",
        summary="获取用户信息",
        description=(
            "通过 access_token 获取当前授权用户的信息。\n"
            "认证方式：Authorization: Bearer <access_token>\n"
            "返回格式符合 OIDC UserInfo 规范。"
        ),
    )
    def userinfo(request: Request):
        source_ip = _get_request_client_ip(request)

        # 从 Authorization 头提取 Bearer Token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "error": "invalid_token",
                    "error_description": "缺少或无效的 Bearer Token",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = auth_header[7:]  # 去掉 "Bearer " 前缀

        try:
            user_info = oauth2_provider_service.get_userinfo(
                access_token,
                source_ip=source_ip,
            )
            return user_info
        except ValueError as e:
            error_msg = str(e)
            if _is_ip_whitelist_error(error_msg):
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "access_denied",
                        "error_description": error_msg,
                    },
                )
            return JSONResponse(
                status_code=401,
                content={
                    "error": "invalid_token",
                    "error_description": error_msg,
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

    # ------------------------------------------------------------------
    # GET /.well-known/oauth-authorization-server — 元数据（可选）
    # ------------------------------------------------------------------
    @router.get(
        "/.well-known/oauth-authorization-server",
        summary="OAuth2 授权服务器元数据",
        description="返回 RFC 8414 授权服务器元数据，便于客户端自动发现端点。",
    )
    def authorization_server_metadata(request: Request):
        issuer = get_oidc_issuer()
        metadata = {
            "issuer": issuer,
            "authorization_endpoint": build_oidc_url("/authorize"),
            "token_endpoint": build_oidc_url("/token"),
            "userinfo_endpoint": build_oidc_url("/userinfo"),
            "response_types_supported": ["code"],
            "grant_types_supported": [
                "authorization_code",
                "refresh_token",
            ],
            "token_endpoint_auth_methods_supported": [
                "client_secret_basic",
                "client_secret_post",
            ],
            "scopes_supported": ["openid", "profile", "email"],
            "subject_types_supported": ["public"],
        }
        if is_rs256_enabled() and get_runtime_jwt_public_key():
            metadata["jwks_uri"] = build_oidc_url("/jwks")
            metadata["id_token_signing_alg_values_supported"] = [settings.jwt.algorithm]
        metadata["code_challenge_methods_supported"] = ["S256"]
        return metadata

    @router.get(
        "/jwks",
        summary="JWKS 公钥端点",
        description="返回 RS256 公钥，供下游系统本地验签。",
    )
    def jwks():
        return build_jwks()

    return router
