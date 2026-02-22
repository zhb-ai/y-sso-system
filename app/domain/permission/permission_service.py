"""权限域 - 服务层

提供权限管理、路由扫描同步、角色权限分配的业务逻辑。

路由扫描配置通过 PermissionRegistry 收集，各模块在 main.py 注册路由时
顺便调用 registry.register() 声明自己的权限模块，无需维护集中式硬编码字典。
"""

from typing import Type, List

from fastapi import FastAPI

from yweb.log import get_logger
from .entities import Permission, RolePermission

logger = get_logger()

# 框架级排除（文档、健康检查等），不需要项目方关心
_FRAMEWORK_EXCLUDED_PREFIXES = [
    "/docs", "/redoc", "/openapi.json",
    "/health",
]
_FRAMEWORK_EXCLUDED_EXACT = ["/"]


class PermissionRegistry:
    """权限模块注册表

    各业务模块在注册路由时调用 register() 声明自己的权限信息，
    公共端点调用 exclude() 标记不纳入权限管理。

    用法（在 main.py 中）::

        perm_registry = PermissionRegistry()

        app.include_router(role_router, prefix="/api/v1", ...)
        perm_registry.register("/api/v1/roles", "角色管理", "role")

        perm_registry.exclude("/api/v1/auth")
    """

    def __init__(self):
        self._modules = {}
        self._excluded_prefixes = []

    def register(self, route_prefix: str, module_name: str, code_prefix: str):
        """注册一个权限模块，register之后就被列入权限管理，有权限的角色才能访问

        Args:
            route_prefix: 路由前缀，如 "/api/v1/roles"
            module_name: 模块显示名称，如 "角色管理"
            code_prefix: 权限编码前缀，如 "role"
        """
        self._modules[route_prefix] = (module_name, code_prefix)

    def exclude(self, *prefixes: str):
        """排除不纳入权限管理的路由前缀，任何用户都可以访问

        Args:
            *prefixes: 一个或多个路由前缀，如 "/api/v1/auth"
        """
        self._excluded_prefixes.extend(prefixes)

    @property
    def module_registry(self) -> dict:
        return dict(self._modules)

    @property
    def excluded_prefixes(self) -> list:
        return self._excluded_prefixes + _FRAMEWORK_EXCLUDED_PREFIXES


class PermissionService:
    """权限管理服务

    处理权限查询、路由扫描同步、角色权限分配：
    - 权限树查询
    - 路由扫描并同步到权限表
    - 角色权限查询与全量设置
    """

    def __init__(
        self,
        app_instance: FastAPI,
        role_model: Type,
        registry: PermissionRegistry,
    ):
        """
        Args:
            app_instance: FastAPI 应用实例（用于路由扫描）
            role_model: 角色模型类
            registry: 权限模块注册表
        """
        self.app_instance = app_instance
        self.role_model = role_model
        self.registry = registry

    # ==================== 权限查询 ====================

    def get_permission_tree(self) -> list:
        """获取按模块分组的权限树

        Returns:
            [{"module": "应用管理", "permissions": [Permission, ...]}, ...]
        """
        tree = Permission.get_module_tree()
        return [
            {"module": module_name, "permissions": perms}
            for module_name, perms in tree.items()
        ]

    # ==================== 路由扫描 ====================

    def _scan_routes(self) -> List[dict]:
        """扫描 FastAPI 路由，生成模块级权限条目

        策略：模块级权限，每个路由组只生成一条 `module:manage` 权限。
        只有在 registry 中注册过且在实际路由中存在的模块才会被识别。

        Returns:
            [{"code": "application:manage", "name": "应用管理", "module": "应用管理", ...}, ...]
        """
        module_registry = self.registry.module_registry
        excluded_prefixes = self.registry.excluded_prefixes
        discovered_modules = set()
        result = []

        # 从 OpenAPI schema 中获取所有路径（最可靠的方式）
        try:
            paths = list(self.app_instance.openapi().get("paths", {}).keys())
        except Exception:
            paths = [getattr(r, 'path', '') for r in self.app_instance.routes]

        for path in paths:
            if path in _FRAMEWORK_EXCLUDED_EXACT:
                continue
            if any(path.startswith(prefix) for prefix in excluded_prefixes):
                continue

            for prefix, (module_name, code_prefix) in module_registry.items():
                if path.startswith(prefix) and module_name not in discovered_modules:
                    discovered_modules.add(module_name)
                    result.append({
                        "code": f"{code_prefix}:manage",
                        "name": module_name,
                        "module": module_name,
                        "description": f"{module_name}模块的管理权限",
                    })
                    break

        result.sort(key=lambda x: x["module"])
        return result

    def scan_and_sync(self) -> dict:
        """扫描路由并同步权限到数据库

        Returns:
            {"scanned": int, "created": [...], "skipped": [...]}

        Raises:
            ValueError: 扫描或同步过程异常
        """
        scanned = self._scan_routes()
        created = []
        skipped = []

        for item in scanned:
            existing = Permission.get_by_code(item["code"])
            if existing:
                skipped.append(item["code"])
                continue

            perm = Permission(
                code=item["code"],
                name=item["name"],
                module=item["module"],
                description=item["description"],
                sort_order=0,
            )
            perm.add(commit=True)
            created.append(item["code"])
            logger.info(f"权限创建: {item['code']} ({item['name']})")

        return {
            "scanned": len(scanned),
            "created": created,
            "skipped": skipped,
        }

    # ==================== 角色权限管理 ====================

    def get_role_permissions(self, role_code: str) -> list:
        """获取角色已关联的权限列表

        Args:
            role_code: 角色编码

        Returns:
            Permission 实体列表

        Raises:
            ValueError: 角色不存在
        """
        role = self.role_model.get_by_code(role_code)
        if not role:
            raise ValueError(f"角色不存在: {role_code}")

        perm_codes = RolePermission.get_role_permission_codes(role.id)
        all_perms = Permission.list_all()
        return [p for p in all_perms if p.code in perm_codes]

    def set_role_permissions(self, role_code: str, permission_ids: List[int]) -> None:
        """全量设置角色权限

        Args:
            role_code: 角色编码
            permission_ids: 权限ID列表

        Raises:
            ValueError: 角色不存在
        """
        role = self.role_model.get_by_code(role_code)
        if not role:
            raise ValueError(f"角色不存在: {role_code}")

        RolePermission.set_role_permissions(role.id, permission_ids)
        logger.info(f"角色权限已更新: {role_code}, permissions={permission_ids}")
