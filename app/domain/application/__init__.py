"""应用域 - SSO 客户端应用管理

提供 SSO 客户端应用的注册、配置、OAuth2 令牌管理等功能。

领域模型：
    - Application: SSO 客户端应用
    - ApplicationPermission: 应用-角色权限
    - OAuth2Token: OAuth2 令牌

服务层：
    - ApplicationService: 应用管理
    - OAuth2TokenService: 令牌管理
"""

from .entities import Application, ApplicationPermission, OAuth2Token
from .services import ApplicationService, OAuth2TokenService

__all__ = [
    "Application",
    "ApplicationPermission",
    "OAuth2Token",
    "ApplicationService",
    "OAuth2TokenService",
]
