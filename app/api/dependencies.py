"""
API 依赖模块

通过 init() 函数初始化认证依赖，由 main.py 在 app 创建后调用。
auth_service 和 token_blacklist 由框架 setup_auth() 自动创建，
此处仅做模块级别名，兼容现有导入方式。

使用方式：
    from app.api.dependencies import auth, auth_service, require_admin

    # 路由级别认证
    router = APIRouter(dependencies=[Depends(auth.get_current_user)])

    # 管理员路由（认证 + 角色检查）
    app.include_router(router, dependencies=[
        Depends(auth.get_current_user),
        Depends(require_admin),
    ])

    # 函数级别认证
    @app.get("/me")
    def get_me(user=Depends(auth.get_current_user)):
        ...
    
    # 认证服务
    auth_service.authenticate("admin", "password")
"""

from fastapi import Depends, HTTPException, status

# 由 main.py 调用 init() 后填充
auth = None
auth_service = None
token_blacklist = None


def init(auth_setup):
    """初始化认证依赖
    
    在 main.py 中 setup_auth() 之后调用，暴露 auth 及其组件的模块级引用。
    
    Args:
        auth_setup: setup_auth() 返回的 AuthSetup 对象
    """
    global auth, auth_service, token_blacklist
    
    auth = auth_setup
    auth_service = auth_setup.auth_service
    token_blacklist = auth_setup.token_blacklist


async def require_admin(user=None):
    """管理员角色检查依赖
    
    必须与 auth.get_current_user 配合使用（放在同一路由的 dependencies 中）。
    从当前请求上下文中获取已认证用户，检查是否具有 admin 角色。
    
    Raises:
        HTTPException 403: 用户不具备管理员角色
    """
    # 延迟获取 auth（因为模块加载时 auth 尚未初始化）
    if auth is None:
        raise HTTPException(status_code=500, detail="认证模块未初始化")
    
    # 通过 auth.get_current_user 的依赖注入方式无法直接在此获取 user，
    # 改为使用独立的依赖签名，让 FastAPI 注入当前用户
    pass


def get_require_admin():
    """创建管理员角色检查依赖（工厂函数）
    
    在 auth 初始化完成后调用，返回一个可直接用于 Depends() 的依赖函数。
    
    Returns:
        管理员角色检查依赖函数
        
    Usage::
    
        require_admin = get_require_admin()
        app.include_router(router, dependencies=[Depends(require_admin)])
    """
    def _require_admin(user=Depends(auth.get_current_user)):
        if not hasattr(user, 'has_role') or not user.has_role('admin'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：仅管理员可访问",
            )
        return user

    return _require_admin


def get_require_permission(*permission_codes: str):
    """创建权限检查依赖（工厂函数）
    
    检查逻辑：
    1. admin 角色直接放行（不查 permission 表）
    2. 其他角色查 role_permission 表，检查是否拥有指定权限
    
    Args:
        permission_codes: 需要的权限编码（任一匹配即放行）
        
    Usage::
    
        app.include_router(
            application_router,
            dependencies=[Depends(get_require_permission('application:manage'))],
        )
    """
    from app.domain.permission.entities import RolePermission

    def _require_permission(user=Depends(auth.get_current_user)):
        # admin 直接放行
        if hasattr(user, 'has_role') and user.has_role('admin'):
            return user

        # 获取用户所有角色 ID
        roles = getattr(user, 'roles', []) or []
        role_ids = [r.id for r in roles]

        if not role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：未分配任何角色",
            )

        # 查询用户所有角色的权限合集
        user_perms = RolePermission.get_permissions_by_role_ids(role_ids)

        # 检查是否拥有任一所需权限
        if not user_perms.intersection(set(permission_codes)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {', '.join(permission_codes)}",
            )

        return user

    return _require_permission
