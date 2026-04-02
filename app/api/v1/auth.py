"""项目特有的认证路由

标准认证端点（登录/登出/刷新令牌/踢出用户）已由 yweb 框架通过
setup_auth(auth_routes=True) 自动挂载到 /api/v1/auth/* 下。

此文件保留项目特有的认证路由（如自助修改密码、企业微信登录）。

端点列表：
    POST /auth/change-password               用户自助修改密码
    GET  /auth/wechat-work/login-config      获取企微扫码登录参数
    POST /auth/wechat-work/login             企微授权码登录（扫码/企微内部通用）
    GET  /auth/wechat-work/oauth-url         获取企微内部静默授权 URL
"""

from typing import Optional

from fastapi import APIRouter, Query, Depends, Request
from pydantic import BaseModel, Field
from yweb.response import Resp, OkResponse


def create_project_auth_router(
    get_current_user,
    auth_app_service,
    wechat_auth_service=None,
) -> APIRouter:
    """创建项目特有的认证路由

    Args:
        get_current_user: 认证依赖（由 setup_auth 提供）
        auth_app_service: 认证应用服务（处理密码操作）
        wechat_auth_service: 企微登录应用服务（处理企微扫码/静默授权）

    Returns:
        APIRouter
    """

    router = APIRouter(
        prefix="/auth",
        tags=["auth"],
    )

    # ==================== DTO ====================

    class ChangePasswordRequest(BaseModel):
        """修改密码请求"""
        old_password: str = Field(..., description="当前密码")
        new_password: str = Field(..., min_length=6, max_length=128, description="新密码")

    class WechatWorkLoginRequest(BaseModel):
        """企业微信登录请求"""
        code: str = Field(..., description="企微授权码（auth_code 或 oauth code）")

    # ==================== 自助修改密码 ====================

    @router.post("/change-password", response_model=OkResponse, summary="修改密码")
    def change_password(data: ChangePasswordRequest, user=Depends(get_current_user)):
        """用户自助修改密码

        验证旧密码后设置新密码，同时清除「首次登录强制修改」标记。
        """
        try:
            auth_app_service.change_password(user, data.old_password, data.new_password)
            return Resp.OK(message="密码修改成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    # ==================== 企业微信登录 ====================

    @router.get(
        "/wechat-work/login-config",
        response_model=OkResponse,
        summary="获取企微扫码登录参数",
        description="返回前端渲染企微 Web 登录组件所需的参数",
    )
    def wechat_work_login_config(request: Request):
        """获取企微扫码登录参数"""
        if not wechat_auth_service:
            return Resp.OK(data={"enabled": False})

        base_url = str(request.base_url).rstrip("/")
        data = wechat_auth_service.get_login_config(base_url)
        return Resp.OK(data=data)

    @router.post(
        "/wechat-work/login",
        response_model=OkResponse,
        summary="企微授权码登录",
        description="用企微授权码（扫码或企微内部授权均可）换取本系统 JWT Token",
    )
    def wechat_work_login(data: WechatWorkLoginRequest, request: Request):
        """企微授权码登录"""
        try:
            if not wechat_auth_service:
                raise ValueError("企微登录服务未初始化")

            ip_address = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "")

            result = wechat_auth_service.login_by_code(
                code=data.code,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return Resp.OK(data=result, message="企业微信登录成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.get(
        "/wechat-work/oauth-url",
        response_model=OkResponse,
        summary="获取企微内部静默授权 URL",
        description="在企业微信内部打开时，通过此接口获取静默授权跳转链接，实现免登录",
    )
    def wechat_work_oauth_url(
        redirect_uri: str = Query(..., description="授权成功后的前端回调地址"),
        state: Optional[str] = Query("", description="状态参数"),
    ):
        """获取企微内部静默授权 URL"""
        try:
            if not wechat_auth_service:
                raise ValueError("企微登录服务未初始化")

            result = wechat_auth_service.get_oauth_url(redirect_uri, state)
            return Resp.OK(data=result)
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    return router
