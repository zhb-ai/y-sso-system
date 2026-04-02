"""项目特有的用户管理扩展 API

标准用户 CRUD（列表/详情/创建/更新/启用/禁用/重置密码）已由 yweb 框架通过
setup_auth(app=app) 自动挂载到 /api/v1/users/* 下。

此文件保留项目特有的用户管理端点（如强制重置密码为固定临时密码）。

端点列表：
    POST /force-reset-password  强制重置用户密码为临时密码（000000）
"""

from fastapi import APIRouter, Query
from pydantic import Field

from yweb import DTO
from yweb.response import Resp, ItemResponse

from app.services.auth_app import AuthApplicationService


def create_project_user_router() -> APIRouter:
    """创建项目特有的用户管理路由

    Returns:
        APIRouter
    """

    router = APIRouter()
    auth_app_service = AuthApplicationService()

    # ==================== DTO ====================

    class ForceResetPasswordResponse(DTO):
        """强制重置密码响应"""
        password: str = Field(..., description="临时密码")

    # ==================== 强制重置密码 ====================

    @router.post(
        "/force-reset-password",
        response_model=ItemResponse[ForceResetPasswordResponse],
        summary="强制重置用户密码",
    )
    def force_reset_password(
        user_id: int = Query(..., description="用户ID"),
    ):
        """重置用户密码为临时密码（000000），并标记首次登录需修改密码

        重置后用户首次登录时需强制修改密码。
        """
        try:
            temp_password = auth_app_service.force_reset_password(user_id)
            return Resp.OK(
                ForceResetPasswordResponse(password=temp_password),
                message="密码重置成功",
            )
        except ValueError as e:
            return Resp.NotFound(message=str(e))

    return router
