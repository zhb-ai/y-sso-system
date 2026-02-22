"""权限管理 API

提供权限列表（树形）、路由自动扫描、角色权限分配等功能。
使用动词风格路由。

端点列表：
    GET  /permissions/tree            → 权限树（按模块分组）
    POST /permissions/scan            → 自动扫描 FastAPI 路由，同步到 permission 表
    GET  /roles/permissions           → 获取角色已分配的权限编码列表
    POST /roles/set-permissions       → 全量设置角色权限
"""

from typing import Optional, List, Type

from fastapi import APIRouter, Query, FastAPI
from pydantic import BaseModel, Field

from yweb import DTO
from yweb.response import Resp, ItemResponse, OkResponse

from app.domain.permission.permission_service import PermissionService, PermissionRegistry


def create_permission_router(
    app_instance: FastAPI,
    role_model: Type,
    registry: PermissionRegistry,
) -> APIRouter:
    """创建权限管理路由

    Args:
        app_instance: FastAPI 应用实例（用于路由扫描）
        role_model: 角色模型类
        registry: 权限模块注册表

    Returns:
        APIRouter
    """

    router = APIRouter()
    perm_service = PermissionService(
        app_instance=app_instance,
        role_model=role_model,
        registry=registry,
    )

    # ==================== DTO ====================

    class PermissionResponse(DTO):
        """权限响应"""
        id: int = 0
        code: str = ""
        name: str = ""
        module: str = ""
        description: Optional[str] = None
        sort_order: int = 0

    class SetPermissionsRequest(BaseModel):
        """设置角色权限请求"""
        permission_ids: List[int] = Field(..., description="权限ID列表")

    # ==================== 权限查询 ====================

    @router.get(
        "/permissions/tree",
        response_model=OkResponse,
        summary="获取权限树（按模块分组）",
    )
    async def get_permission_tree():
        """获取所有权限，按模块分组为树形结构"""
        tree = perm_service.get_permission_tree()
        result = [
            {
                "module": group["module"],
                "permissions": PermissionResponse.from_list(group["permissions"]),
            }
            for group in tree
        ]
        return Resp.OK(result)

    # ==================== 路由扫描 ====================

    @router.post(
        "/permissions/scan",
        response_model=OkResponse,
        summary="自动扫描路由，同步到权限表",
        description="扫描 FastAPI 已注册路由，自动生成模块级权限条目。已存在的权限不会重复创建。",
    )
    async def scan_permissions():
        """扫描路由并同步权限"""
        try:
            result = perm_service.scan_and_sync()
            return Resp.OK(result, message=f"扫描完成，新增 {len(result['created'])} 个权限")
        except Exception as e:
            return Resp.BadRequest(message=str(e))

    # ==================== 角色权限管理 ====================

    @router.get(
        "/roles/permissions",
        response_model=ItemResponse[PermissionResponse],
        summary="获取角色已分配的权限",
    )
    async def get_role_permissions(
        code: str = Query(..., description="角色编码"),
    ):
        """获取角色已关联的权限列表"""
        try:
            perms = perm_service.get_role_permissions(code)
            return Resp.OK(PermissionResponse.from_list(perms))
        except ValueError as e:
            return Resp.NotFound(message=str(e))

    @router.post(
        "/roles/set-permissions",
        response_model=OkResponse,
        summary="设置角色权限（全量覆盖）",
    )
    async def set_role_permissions(
        data: SetPermissionsRequest,
        code: str = Query(..., description="角色编码"),
    ):
        """全量设置角色权限，传入权限 ID 列表"""
        try:
            perm_service.set_role_permissions(code, data.permission_ids)
            return Resp.OK(message="权限设置成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    return router
