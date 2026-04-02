"""角色管理 API

提供角色 CRUD、用户角色分配等功能。
基于 yweb.auth 的轻量级 Role 模型，使用动词风格路由。

设计原则：
- 角色模型由 setup_auth(role_model=True) 自动创建
- 本模块通过 create_role_router(role_model, user_model) 工厂函数创建路由
- 路由挂载和认证依赖由 main.py 统一管理

端点列表：
    GET  /roles/list              → 角色列表
    GET  /roles/get               → 角色详情
    POST /roles/create            → 创建角色
    POST /roles/update            → 更新角色
    POST /roles/delete            → 删除角色（软删除）
    GET  /roles/users             → 获取某角色下的用户列表
    POST /users/assign-role       → 给用户分配角色
    POST /users/unassign-role     → 移除用户角色
    GET  /users/roles             → 获取用户的角色列表
"""

from typing import Optional, List, Type

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, field_validator

from yweb import DTO
from yweb.response import Resp, ItemResponse, OkResponse
from app.domain.auth.role_service import RoleService


def create_role_router(role_model: Type, user_model: Type) -> APIRouter:
    """创建角色管理路由

    Args:
        role_model: 角色模型类（由 setup_auth 自动创建）
        user_model: 用户模型类

    Returns:
        APIRouter 包含角色 CRUD 和用户角色管理端点
    """

    router = APIRouter()
    role_service = RoleService(role_model=role_model, user_model=user_model)

    # ==================== DTO ====================

    class RoleResponse(DTO):
        """角色响应"""
        id: int = 0
        name: str = ""
        code: str = ""
        description: Optional[str] = None
        created_at: Optional[str] = None
        updated_at: Optional[str] = None

    class RoleCreateRequest(BaseModel):
        """创建角色请求"""
        name: str = Field(..., min_length=1, max_length=100, description="角色名称")
        code: str = Field(..., min_length=1, max_length=50, description="角色编码")
        description: Optional[str] = Field(None, max_length=500, description="角色描述")

    class RoleUpdateRequest(BaseModel):
        """更新角色请求"""
        name: Optional[str] = Field(None, min_length=1, max_length=100, description="角色名称")
        description: Optional[str] = Field(None, max_length=500, description="角色描述")

    class AssignRoleRequest(BaseModel):
        """分配角色请求"""
        user_id: int = Field(..., description="用户ID")
        role_code: str = Field(..., description="角色编码")

    class UserRoleResponse(DTO):
        """用户角色响应"""
        id: int = 0
        username: str = ""
        name: Optional[str] = None
        email: Optional[str] = None
        roles: List[str] = []

        @field_validator('roles', mode='before')
        @classmethod
        def convert_roles(cls, v):
            """将 Role ORM 对象列表转换为角色编码字符串列表"""
            if not v:
                return []
            return [r.code if hasattr(r, 'code') else str(r) for r in v]

    # ==================== 角色 CRUD ====================

    @router.get(
        "/roles/list",
        response_model=ItemResponse[RoleResponse],
        summary="获取角色列表",
        description="获取所有角色（轻量模型，不分页）",
    )
    def list_roles():
        """获取角色列表"""
        roles = role_service.list_roles()
        return Resp.OK(RoleResponse.from_list(roles))

    @router.get(
        "/roles/get",
        response_model=ItemResponse[RoleResponse],
        summary="获取角色详情",
    )
    def get_role(
        code: str = Query(..., description="角色编码"),
    ):
        """根据角色编码获取详情"""
        try:
            role = role_service.get_role(code)
            return Resp.OK(RoleResponse.from_entity(role))
        except ValueError as e:
            return Resp.NotFound(message=str(e))

    @router.post(
        "/roles/create",
        response_model=ItemResponse[RoleResponse],
        summary="创建角色",
    )
    def create_role(data: RoleCreateRequest):
        """创建角色"""
        try:
            role = role_service.create_role(
                name=data.name,
                code=data.code,
                description=data.description,
            )
            return Resp.OK(RoleResponse.from_entity(role), message="角色创建成功")
        except ValueError as e:
            return Resp.Conflict(message=str(e))

    @router.post(
        "/roles/update",
        response_model=ItemResponse[RoleResponse],
        summary="更新角色",
    )
    def update_role(
        data: RoleUpdateRequest,
        code: str = Query(..., description="角色编码"),
    ):
        """更新角色信息"""
        try:
            update_data = data.model_dump(exclude_unset=True)
            role = role_service.update_role(code, **update_data)
            return Resp.OK(RoleResponse.from_entity(role), message="更新成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.post(
        "/roles/delete",
        response_model=OkResponse,
        summary="删除角色",
    )
    def delete_role(
        code: str = Query(..., description="角色编码"),
    ):
        """删除角色（软删除）"""
        try:
            role_service.delete_role(code)
            return Resp.OK(message="删除成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    # ==================== 用户角色管理 ====================

    @router.get(
        "/roles/users",
        response_model=ItemResponse[UserRoleResponse],
        summary="获取某角色下的用户列表",
    )
    def list_role_users(
        code: str = Query(..., description="角色编码"),
    ):
        """获取拥有指定角色的所有用户"""
        try:
            users = role_service.list_role_users(code)
            return Resp.OK(UserRoleResponse.from_list(users))
        except ValueError as e:
            return Resp.NotFound(message=str(e))

    @router.post(
        "/users/assign-role",
        response_model=OkResponse,
        summary="给用户分配角色",
    )
    def assign_role(data: AssignRoleRequest):
        """给用户分配角色"""
        try:
            role_service.assign_role(
                user_id=data.user_id,
                role_code=data.role_code,
            )
            return Resp.OK(message="角色分配成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.post(
        "/users/unassign-role",
        response_model=OkResponse,
        summary="移除用户角色",
    )
    def unassign_role(data: AssignRoleRequest):
        """移除用户的指定角色"""
        try:
            role_service.unassign_role(
                user_id=data.user_id,
                role_code=data.role_code,
            )
            return Resp.OK(message="角色移除成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.get(
        "/users/roles",
        response_model=ItemResponse[RoleResponse],
        summary="获取用户的角色列表",
    )
    def list_user_roles(
        user_id: int = Query(..., description="用户ID"),
    ):
        """获取指定用户的所有角色"""
        try:
            roles = role_service.list_user_roles(user_id)
            return Resp.OK(RoleResponse.from_list(roles))
        except ValueError as e:
            return Resp.NotFound(message=str(e))

    return router
