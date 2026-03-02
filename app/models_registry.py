"""统一模型注册中心

所有入口点（main.py / init_db.py / alembic/env.py）都应通过此模块注册模型，
确保 BaseModel.metadata 中包含项目的全部表定义，避免遗漏。

使用方式：
=========

场景1：main.py（有 FastAPI app，需要路由挂载）
    from app.models_registry import User, LoginRecord, EmployeeUserMixin
    # 继续使用 setup_auth(app=app, ...) 和 setup_organization(app=app, ...)

场景2：init_db.py / alembic/env.py（无 FastAPI app，只需模型注册）
    from app.models_registry import ensure_dynamic_models
    registry = ensure_dynamic_models()
    Role = registry.role_model
"""

# ======================== 1. 静态模型（导入即注册到 metadata） ========================

from app.domain.auth.model.user import User                                     # noqa: F401
from app.domain.auth.model.login_record import LoginRecord                      # noqa: F401
from app.domain.application.entities import (                                   # noqa: F401
    Application, ApplicationPermission, OAuth2Token, AuthorizationCode,
)
from app.domain.permission.entities import Permission, RolePermission           # noqa: F401
from app.domain.sso_role.entities import SSORole, UserSSORole                   # noqa: F401
from app.domain.config.entities import SystemConfig                             # noqa: F401


# ======================== 2. 共享配置（各入口复用） ========================

from yweb.orm import fields
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional


class EmployeeUserMixin:
    """员工关联用户账号 — 所有入口共享此定义"""
    user = fields.OneToOne(User, on_delete=fields.DO_NOTHING, nullable=True)
    
    enterprise_wechat_user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="企业微信用户ID")
    enterprise_wechat_openid: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="企业微信OpenID")


class EmployeeOrgRelMixin:
    """员工-组织关联扩展 — 企业微信相关字段"""
    enterprise_wechat_openid: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="企业微信OpenID")


# ======================== 3. 应用级组织模型（Web 场景复用 setup_organization 的产出） ========================

_app_org_models = None


def set_app_org_models(org_models):
    """由 register_all_routes 在 setup_organization 后调用，供 AuthServiceImpl 等复用"""
    global _app_org_models
    _app_org_models = org_models


def get_app_org_models():
    """获取应用级组织模型（Web 场景下由 setup_organization 创建）"""
    return _app_org_models


# ======================== 4. 动态模型注册 ========================

class _DynamicModelsRegistry:
    """动态模型注册结果容器"""
    def __init__(self, auth_setup, org_models):
        self._auth = auth_setup
        self._org = org_models

    @property
    def role_model(self):
        return self._auth.role_model

    @property
    def org_models(self):
        return self._org


_cached_registry = None


def ensure_dynamic_models() -> _DynamicModelsRegistry:
    """确保动态模型已注册到 metadata（幂等，多次调用返回同一结果）

    仅用于 init_db.py / alembic/env.py 等脱离 main.py 的场景。
    main.py 不需要调用此函数（setup_auth / setup_organization 会自行创建）。

    创建的动态模型：
        - Role + user_role 关联表（由 setup_auth 创建）
        - Organization / Department / Employee 等组织架构表（由 create_org_models 创建）
    """
    global _cached_registry
    if _cached_registry is not None:
        return _cached_registry

    # Role + user_role
    from yweb.auth import setup_auth
    auth = setup_auth(user_model=User, role_model=True)

    # 组织架构 6 张表
    from yweb.organization import create_org_models
    org = create_org_models(
        employee_mixin=EmployeeUserMixin,
        emp_org_rel_mixin=EmployeeOrgRelMixin,
    )

    _cached_registry = _DynamicModelsRegistry(auth, org)
    return _cached_registry
