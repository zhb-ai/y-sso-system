"""SSO 门户 API

提供已登录用户可访问的应用列表（仅需认证，无需管理权限）。

端点列表：
    GET  /sso/apps         获取可用应用列表（SSO 门户）
    POST /sso/bip/launch   按应用编码 bip 获取 BIP 登录地址
"""

import json

from fastapi import APIRouter, Depends

from yweb import DTO
from yweb.response import Resp, OkResponse, ItemResponse

from app.services.bip_launch import BIP_APP_CODE, BipLaunchService


def create_sso_portal_router(application_model, get_current_user=None) -> APIRouter:
    """创建 SSO 门户路由

    Args:
        application_model: 应用模型类

    Returns:
        APIRouter 实例
    """

    router = APIRouter(prefix="/sso", tags=["SSO 门户"])

    @router.get(
        "/apps",
        response_model=OkResponse,
        summary="获取可用应用列表（SSO 门户）",
    )
    def sso_available_apps():
        """SSO 门户：获取所有激活的应用列表

        仅需要登录认证，不需要管理权限。
        返回字段精简，只包含门户展示所需的信息。
        """
        apps = application_model.query.filter_by(is_active=True).all()
        result = []
        for app_item in apps:
            uris = app_item.redirect_uris
            if isinstance(uris, str):
                try:
                    uris = json.loads(uris)
                except (json.JSONDecodeError, TypeError):
                    uris = []
            code = getattr(app_item, "code", "") or ""
            if not uris and code != BIP_APP_CODE:
                continue
            result.append({
                "id": app_item.id,
                "name": app_item.name,
                "code": getattr(app_item, 'code', ''),
                "description": getattr(app_item, 'description', ''),
                "client_id": app_item.client_id,
                "redirect_uris": uris,
                "logo_url": getattr(app_item, 'logo_url', None),
            })
        return Resp.OK(result)

    class BipLaunchResponse(DTO):
        """BIP 一次性登录地址"""
        login_url: str = ""

    def _uninjected_user():
        raise RuntimeError("未注入当前用户")

    current_user_dep = get_current_user or _uninjected_user

    @router.post(
        "/bip/launch",
        response_model=ItemResponse[BipLaunchResponse],
        summary="获取 BIP 单点登录地址",
    )
    def launch_bip(user=Depends(current_user_dep)):
        """已登录用户进入应用编码为 bip 的系统。"""
        try:
            login_url = BipLaunchService(application_model).launch(user)
            return Resp.OK(BipLaunchResponse(login_url=login_url))
        except ValueError as exc:
            return Resp.BadRequest(message=str(exc))

    return router
