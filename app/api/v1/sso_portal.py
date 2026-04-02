"""SSO 门户 API

提供已登录用户可访问的应用列表（仅需认证，无需管理权限）。

端点列表：
    GET /sso/apps  获取可用应用列表（SSO 门户）
"""

import json

from fastapi import APIRouter

from yweb.response import Resp, OkResponse


def create_sso_portal_router(application_model) -> APIRouter:
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
            if not uris:
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

    return router
