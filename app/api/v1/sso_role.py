"""SSO 角色管理 API

提供 SSO 角色 CRUD 和用户 SSO 角色分配等功能。
SSO 角色用于同步给外部系统，与系统内部的 auth 角色相互独立。

端点列表：
    GET  /sso-roles/list              → SSO 角色列表
    GET  /sso-roles/get               → SSO 角色详情
    POST /sso-roles/create            → 创建 SSO 角色
    POST /sso-roles/update            → 更新 SSO 角色
    POST /sso-roles/delete            → 删除 SSO 角色（软删除）
    GET  /sso-roles/user-roles        → 获取用户的 SSO 角色列表
    POST /sso-roles/assign            → 给用户分配 SSO 角色
    POST /sso-roles/unassign          → 移除用户的 SSO 角色
    POST /sso-roles/set-user-roles    → 全量设置用户的 SSO 角色
"""

from typing import Optional, List

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from yweb import DTO
from yweb.response import Resp, ItemResponse, OkResponse

from app.domain.sso_role.sso_role_service import SSORoleService


def create_sso_role_router() -> APIRouter:
    """创建 SSO 角色管理路由"""

    router = APIRouter(prefix="/sso-roles")
    sso_role_service = SSORoleService()

    # ==================== DTO ====================

    class SSORoleResponse(DTO):
        """SSO 角色响应"""
        id: int = 0
        code: str = ""
        name: str = ""
        description: Optional[str] = None
        is_active: bool = True
        sort_order: int = 0
        created_at: Optional[str] = None
        updated_at: Optional[str] = None

    class SSORoleCreateRequest(BaseModel):
        """创建 SSO 角色请求"""
        code: str = Field(..., min_length=1, max_length=100, description="角色编码")
        name: str = Field(..., min_length=1, max_length=100, description="角色名称")
        description: Optional[str] = Field(None, max_length=500, description="角色描述")
        sort_order: int = Field(0, ge=0, description="排序序号")

    class SSORoleUpdateRequest(BaseModel):
        """更新 SSO 角色请求"""
        name: Optional[str] = Field(None, min_length=1, max_length=100, description="角色名称")
        description: Optional[str] = Field(None, max_length=500, description="角色描述")
        is_active: Optional[bool] = Field(None, description="是否启用")
        sort_order: Optional[int] = Field(None, ge=0, description="排序序号")

    class AssignSSORoleRequest(BaseModel):
        """分配/移除 SSO 角色请求"""
        user_id: int = Field(..., description="用户ID")
        sso_role_code: str = Field(..., description="SSO 角色编码")

    class SetUserSSORolesRequest(BaseModel):
        """全量设置用户 SSO 角色请求"""
        user_id: int = Field(..., description="用户ID")
        sso_role_codes: List[str] = Field(..., description="SSO 角色编码列表")

    # ==================== SSO 角色 CRUD ====================

    @router.get(
        "/list",
        response_model=ItemResponse[SSORoleResponse],
        summary="获取 SSO 角色列表",
        description="获取所有 SSO 角色，可选仅返回启用的角色",
    )
    def list_sso_roles(
        active_only: bool = Query(False, description="是否仅返回启用的角色"),
    ):
        """获取 SSO 角色列表"""
        roles = sso_role_service.list_roles(active_only=active_only)
        return Resp.OK(SSORoleResponse.from_list(roles))

    @router.get(
        "/get",
        response_model=ItemResponse[SSORoleResponse],
        summary="获取 SSO 角色详情",
    )
    def get_sso_role(
        code: str = Query(..., description="SSO 角色编码"),
    ):
        """根据编码获取 SSO 角色详情"""
        try:
            role = sso_role_service.get_role(code)
            return Resp.OK(SSORoleResponse.from_entity(role))
        except ValueError as e:
            return Resp.NotFound(message=str(e))

    @router.post(
        "/create",
        response_model=ItemResponse[SSORoleResponse],
        summary="创建 SSO 角色",
    )
    def create_sso_role(data: SSORoleCreateRequest):
        """创建 SSO 角色"""
        try:
            role = sso_role_service.create_role(
                code=data.code,
                name=data.name,
                description=data.description,
                sort_order=data.sort_order,
            )
            return Resp.OK(SSORoleResponse.from_entity(role), message="SSO 角色创建成功")
        except ValueError as e:
            return Resp.Conflict(message=str(e))

    @router.post(
        "/update",
        response_model=ItemResponse[SSORoleResponse],
        summary="更新 SSO 角色",
    )
    def update_sso_role(
        data: SSORoleUpdateRequest,
        code: str = Query(..., description="SSO 角色编码"),
    ):
        """更新 SSO 角色"""
        try:
            update_data = data.model_dump(exclude_unset=True)
            role = sso_role_service.update_role(code, **update_data)
            return Resp.OK(SSORoleResponse.from_entity(role), message="更新成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.post(
        "/delete",
        response_model=OkResponse,
        summary="删除 SSO 角色",
    )
    def delete_sso_role(
        code: str = Query(..., description="SSO 角色编码"),
    ):
        """删除 SSO 角色（软删除）"""
        try:
            sso_role_service.delete_role(code)
            return Resp.OK(message="删除成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    # ==================== 用户 SSO 角色管理 ====================

    @router.get(
        "/user-roles",
        response_model=ItemResponse[SSORoleResponse],
        summary="获取用户的 SSO 角色列表",
    )
    def get_user_sso_roles(
        user_id: int = Query(..., description="用户ID"),
    ):
        """获取指定用户的所有 SSO 角色"""
        roles = sso_role_service.get_user_sso_roles(user_id)
        return Resp.OK(SSORoleResponse.from_list(roles))

    @router.post(
        "/assign",
        response_model=OkResponse,
        summary="给用户分配 SSO 角色",
    )
    def assign_sso_role(data: AssignSSORoleRequest):
        """给用户分配 SSO 角色"""
        try:
            sso_role_service.assign_role(
                user_id=data.user_id,
                sso_role_code=data.sso_role_code,
            )
            return Resp.OK(message="SSO 角色分配成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.post(
        "/unassign",
        response_model=OkResponse,
        summary="移除用户的 SSO 角色",
    )
    def unassign_sso_role(data: AssignSSORoleRequest):
        """移除用户的 SSO 角色"""
        try:
            sso_role_service.unassign_role(
                user_id=data.user_id,
                sso_role_code=data.sso_role_code,
            )
            return Resp.OK(message="SSO 角色移除成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.post(
        "/set-user-roles",
        response_model=OkResponse,
        summary="全量设置用户的 SSO 角色",
        description="覆盖式设置，传入空列表则清空用户的所有 SSO 角色",
    )
    def set_user_sso_roles(data: SetUserSSORolesRequest):
        """全量设置用户的 SSO 角色"""
        try:
            sso_role_service.set_user_sso_roles(
                user_id=data.user_id,
                sso_role_codes=data.sso_role_codes,
            )
            return Resp.OK(message="SSO 角色设置成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    return router
