"""路由注册中心

集中管理所有模块的路由注册、认证配置、组织架构初始化、权限注册表。
由 main.py 在应用创建后调用 register_all_routes(app) 完成一站式注册。

注册顺序有依赖关系，请勿随意调整：
    1. 认证模块 (setup_auth)          → 产出 auth 对象
    2. 独立业务路由                    → 仅依赖 auth
    3. 组织架构模块 (setup_organization) → 产出 org 对象
    4. 依赖 org 的路由                 → 需要 org
    5. 权限管理路由（最后注册）          → 需要注册表收集完毕
"""

from fastapi import Depends

from yweb.auth import setup_auth
from yweb.organization import setup_organization
from yweb.log import get_logger

from app.config import settings
from app.models_registry import User, LoginRecord, EmployeeUserMixin, set_app_org_models
from app.domain.auth.impl.auth_service_impl import AuthServiceImpl
from app.domain.permission.permission_service import PermissionRegistry, PermissionService

logger = get_logger()


# ==================== 登录响应构建器 ====================


def _build_login_response(user, access_token, refresh_token):
    """自定义登录响应：在默认响应基础上附带用户角色列表和 SSO 角色"""
    from app.domain.sso_role.entities import UserSSORole

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "is_active": user.is_active,
            "roles": list(user.role_codes) if hasattr(user, 'role_codes') else [],
            "sso_roles": UserSSORole.get_user_sso_role_codes(user.id),
            "must_change_password": getattr(user, 'must_change_password', False),
        },
    }


# ==================== 一站式路由注册 ====================


def register_all_routes(app):
    """注册所有路由、认证模块、组织架构模块、权限注册表

    Args:
        app: FastAPI 应用实例
    """
    import app.api.dependencies as deps

    # ------------------------------------------------------------------
    # 1. 认证模块
    # ------------------------------------------------------------------
    auth = setup_auth(
        app=app,
        user_model=User,
        login_record_model=LoginRecord,
        jwt_settings=settings.jwt,
        api_prefix="/api/v1",
        auth_routes=True,
        auth_service_class=AuthServiceImpl,
        token_blacklist=True,
        enable_kick=True,
        login_response_builder=_build_login_response,
    )

    # 初始化项目级认证依赖（供 middleware 等模块引用）
    deps.init(auth)
    require_admin = deps.get_require_admin()
    require_permission = deps.get_require_permission

    # ------------------------------------------------------------------
    # 2. 权限注册表
    # ------------------------------------------------------------------
    perm_registry = PermissionRegistry()

    # setup_auth 自动挂载的模块：注册权限信息
    perm_registry.register("/api/v1/users", "用户管理", "user")
    perm_registry.register("/api/v1/login-records", "登录记录", "login_record")
    perm_registry.exclude("/api/v1/auth")  # 认证端点，所有人可用

    # ------------------------------------------------------------------
    # 3. 角色管理（仅依赖 auth）
    # ------------------------------------------------------------------
    from app.api.v1.role import create_role_router

    role_router = create_role_router(
        role_model=auth.role_model,
        user_model=User,
    )
    app.include_router(
        role_router,
        prefix="/api/v1",
        tags=["角色管理"],
        dependencies=[Depends(require_permission('role:manage'))],
    )
    perm_registry.register("/api/v1/roles", "角色管理", "role")

    # ------------------------------------------------------------------
    # 4. 用户管理扩展（强制重置密码等）
    # ------------------------------------------------------------------
    from app.api.v1.user import create_project_user_router

    project_user_router = create_project_user_router()
    app.include_router(
        project_user_router,
        prefix="/api/v1/users",
        tags=["用户管理"],
        dependencies=[Depends(require_permission('user:manage'))],
    )

    # ------------------------------------------------------------------
    # 5. 应用管理
    # ------------------------------------------------------------------
    from app.api.v1.application import create_application_router

    application_router = create_application_router()
    app.include_router(
        application_router,
        prefix="/api/v1",
        tags=["应用管理"],
        dependencies=[Depends(require_permission('application:manage'))],
    )
    perm_registry.register("/api/v1/applications", "应用管理", "application")

    # ------------------------------------------------------------------
    # 6. 组织架构模块（产出 org 对象，后续路由依赖它）
    # ------------------------------------------------------------------
    org = setup_organization(
        app=app,
        api_prefix="/api/v1",
        tags=["组织架构"],
        employee_mixin=EmployeeUserMixin,
        dependencies=[Depends(require_permission('organization:manage'))],
    )
    set_app_org_models(org)  # 供 AuthServiceImpl 等复用，避免 ensure_dynamic_models 重复创建模型
    perm_registry.register("/api/v1/org", "组织架构", "organization")

    # ------------------------------------------------------------------
    # 7. 员工账号管理（依赖 org）
    # ------------------------------------------------------------------
    from app.api.v1.employee_account import create_employee_account_router

    employee_account_router = create_employee_account_router(
        employee_model=org.Employee,
    )
    app.include_router(
        employee_account_router,
        prefix="/api/v1",
        tags=["组织架构"],
        dependencies=[Depends(require_permission('organization:manage'))],
    )

    # ------------------------------------------------------------------
    # 8. 企业微信同步（依赖 org，webhook 端点公开）
    # ------------------------------------------------------------------
    from app.api.v1.wechat_work import create_wechat_work_router

    wechat_work_router = create_wechat_work_router(
        org_models=org,
        management_deps=[Depends(require_permission('organization:manage'))],
    )
    app.include_router(
        wechat_work_router,
        prefix="/api/v1",
        tags=["企业微信同步"],
    )
    perm_registry.exclude("/api/v1/wechat-work/webhook")  # 回调端点，企微验签保护

    # ------------------------------------------------------------------
    # 9. 项目特有认证路由（自助修改密码 + 企微登录，依赖 org）
    # ------------------------------------------------------------------
    from app.api.v1.auth import create_project_auth_router
    from app.services.auth_app import AuthApplicationService
    from app.services.wechat_auth_app import WechatAuthAppService

    auth_app_service = AuthApplicationService()
    wechat_auth_service = WechatAuthAppService(
        org_models=org,
        auth_service=auth.auth_service,
        login_response_builder=_build_login_response,
    )

    project_auth_router = create_project_auth_router(
        get_current_user=auth.get_current_user,
        auth_app_service=auth_app_service,
        wechat_auth_service=wechat_auth_service,
    )
    app.include_router(
        project_auth_router,
        prefix="/api/v1",
    )

    # ------------------------------------------------------------------
    # 10. SSO 角色管理
    # ------------------------------------------------------------------
    from app.api.v1.sso_role import create_sso_role_router

    sso_role_router = create_sso_role_router()
    app.include_router(
        sso_role_router,
        prefix="/api/v1",
        tags=["SSO 角色管理"],
        dependencies=[Depends(require_permission('sso_role:manage'))],
    )
    perm_registry.register("/api/v1/sso-roles", "SSO 角色管理", "sso_role")

    # ------------------------------------------------------------------
    # 11. OAuth2 授权服务器（SSO 核心，有自己的认证逻辑）
    # ------------------------------------------------------------------
    from app.api.v1.oauth2 import create_oauth2_provider_router
    from app.domain.application.services import OAuth2ProviderService

    oauth2_provider_service = OAuth2ProviderService(
        jwt_manager=auth.jwt_manager,
        user_getter=auth.user_getter,
    )
    oauth2_router = create_oauth2_provider_router(
        oauth2_provider_service=oauth2_provider_service,
        get_current_user=auth.get_current_user,
        get_current_user_optional=auth.get_current_user_optional,
    )
    app.include_router(
        oauth2_router,
        prefix="/api/v1",
        tags=["OAuth2 授权服务器"],
    )
    perm_registry.exclude("/api/v1/oauth2")  # OAuth2 有自己的认证逻辑

    # ------------------------------------------------------------------
    # 12. 仪表盘
    # ------------------------------------------------------------------
    from app.api.v1.dashboard import create_dashboard_router
    from app.domain.application.entities import Application
    from app.services.dashboard_app import DashboardAppService

    dashboard_service = DashboardAppService(
        user_model=User,
        application_model=Application,
        org_models=org,
    )
    dashboard_router = create_dashboard_router(
        dashboard_service=dashboard_service,
    )
    app.include_router(
        dashboard_router,
        prefix="/api/v1",
        tags=["仪表盘"],
        dependencies=[Depends(require_permission('dashboard:manage'))],
    )
    perm_registry.register("/api/v1/dashboard", "仪表盘", "dashboard")

    # ------------------------------------------------------------------
    # 13. 系统设置
    # ------------------------------------------------------------------
    from app.api.v1.config import create_config_router

    config_router = create_config_router()
    app.include_router(
        config_router,
        prefix="/api/v1",
        tags=["系统设置"],
        dependencies=[Depends(require_admin)],
    )
    perm_registry.register("/api/v1/settings", "系统设置", "settings")

    # ------------------------------------------------------------------
    # 14. 缓存管理（仅管理员）
    # ------------------------------------------------------------------
    from app.api.v1.cache import create_cache_management_router

    cache_router = create_cache_management_router()
    app.include_router(
        cache_router,
        prefix="/api/v1",
        tags=["缓存管理"],
        dependencies=[Depends(require_admin)],
    )
    perm_registry.register("/api/v1/cache", "缓存管理", "cache")

    # ------------------------------------------------------------------
    # 15. SSO 门户（仅需认证，无需管理权限）
    # ------------------------------------------------------------------
    from app.api.v1.sso_portal import create_sso_portal_router

    sso_portal_router = create_sso_portal_router(
        application_model=Application,
    )
    app.include_router(
        sso_portal_router,
        prefix="/api/v1",
        tags=["SSO 门户"],
        dependencies=[Depends(auth.get_current_user)],
    )
    perm_registry.exclude("/api/v1/sso")  # SSO 门户端点，所有已登录用户可用

    # ------------------------------------------------------------------
    # 16. 权限管理（最后注册，确保注册表已收集完毕）
    # ------------------------------------------------------------------
    from app.api.v1.permission import create_permission_router

    perm_registry.register("/api/v1/permissions", "权限管理", "permission")
    permission_router = create_permission_router(
        app_instance=app,
        role_model=auth.role_model,
        registry=perm_registry,
    )
    app.include_router(
        permission_router,
        prefix="/api/v1",
        tags=["权限管理"],
        dependencies=[Depends(require_permission('permission:manage'))],
    )

    # ------------------------------------------------------------------
    # 将权限服务存入 app.state，供启动事件自动扫描使用
    # ------------------------------------------------------------------
    app.state.perm_service = PermissionService(
        app_instance=app,
        role_model=auth.role_model,
        registry=perm_registry,
    )

    logger.info("所有路由注册完成")
