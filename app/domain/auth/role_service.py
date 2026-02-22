"""角色域 - 服务层

提供角色管理和用户角色分配的业务逻辑。
角色模型由 setup_auth(role_model=True) 动态创建，
因此本服务通过构造函数接收模型类。
"""

from typing import Type, List

from yweb.log import get_logger

logger = get_logger()

# 系统内置角色编码，不允许删除
SYSTEM_ROLE_CODES = ('admin', 'user', 'external')


class RoleService:
    """角色管理服务

    处理角色 CRUD 和用户角色分配：
    - 角色创建、更新、删除
    - 用户角色分配、移除
    - 角色/用户关联查询
    """

    def __init__(self, role_model: Type, user_model: Type):
        self.role_model = role_model
        self.user_model = user_model

    # ==================== 角色 CRUD ====================

    def list_roles(self) -> list:
        """获取所有角色列表"""
        return self.role_model.list_all()

    def get_role(self, code: str):
        """根据编码获取角色

        Raises:
            ValueError: 角色不存在
        """
        role = self.role_model.get_by_code(code)
        if not role:
            raise ValueError(f"角色不存在: {code}")
        return role

    def create_role(self, name: str, code: str, description: str = None):
        """创建角色

        Args:
            name: 角色名称
            code: 角色编码（唯一）
            description: 角色描述

        Returns:
            创建的角色实体

        Raises:
            ValueError: 编码已存在
        """
        existing = self.role_model.get_by_code(code)
        if existing:
            raise ValueError(f"角色编码已存在: {code}")

        role = self.role_model.create_role(
            name=name,
            code=code,
            description=description,
        )
        logger.info(f"角色创建成功: {role.code} ({role.name})")
        return role

    def update_role(self, code: str, **kwargs):
        """更新角色

        Args:
            code: 角色编码
            **kwargs: 要更新的字段

        Returns:
            更新后的角色实体

        Raises:
            ValueError: 角色不存在
        """
        role = self.get_role(code)

        for key, value in kwargs.items():
            setattr(role, key, value)
        role.save(commit=True)

        logger.info(f"角色更新成功: {role.code}")
        return role

    def delete_role(self, code: str) -> None:
        """删除角色（软删除）

        Raises:
            ValueError: 角色不存在 / 系统内置角色不允许删除
        """
        role = self.get_role(code)

        if role.code in SYSTEM_ROLE_CODES:
            raise ValueError(f"系统内置角色不允许删除: {role.code}")

        # 先保存角色代码，删除后对象会过期
        role_code = role.code
        role.soft_delete()
        role.save(commit=True)
        logger.info(f"角色已删除: {role_code}")

    # ==================== 用户角色管理 ====================

    def list_role_users(self, code: str) -> list:
        """获取拥有指定角色的所有用户

        Raises:
            ValueError: 角色不存在
        """
        role = self.get_role(code)

        users = self.user_model.query.filter(
            self.user_model.roles.any(self.role_model.id == role.id)
        ).all()
        return users

    def assign_role(self, user_id: int, role_code: str) -> None:
        """给用户分配角色

        Raises:
            ValueError: 用户不存在 / 角色不存在 / 用户已拥有该角色
        """
        user = self.user_model.get(user_id)
        if not user:
            raise ValueError(f"用户不存在: ID={user_id}")

        role = self.get_role(role_code)

        if hasattr(user, 'has_role') and user.has_role(role_code):
            raise ValueError(f"用户已拥有角色: {role_code}")

        user.add_role(role)
        user.save(commit=True)
        logger.info(f"角色分配成功: user={user.username}, role={role.code}")

    def unassign_role(self, user_id: int, role_code: str) -> None:
        """移除用户角色

        Raises:
            ValueError: 用户不存在 / 角色不存在 / 用户未拥有该角色
        """
        user = self.user_model.get(user_id)
        if not user:
            raise ValueError(f"用户不存在: ID={user_id}")

        role = self.get_role(role_code)

        # 保护：禁止移除 admin 用户的 admin 角色
        if getattr(user, 'username', None) == 'admin' and role_code == 'admin':
            raise ValueError("禁止移除 admin 用户的管理员角色")

        if hasattr(user, 'has_role') and not user.has_role(role_code):
            raise ValueError(f"用户未拥有角色: {role_code}")

        user.remove_role(role)
        user.save(commit=True)
        logger.info(f"角色移除成功: user={user.username}, role={role.code}")

    def list_user_roles(self, user_id: int) -> list:
        """获取指定用户的所有角色

        Raises:
            ValueError: 用户不存在
        """
        user = self.user_model.get(user_id)
        if not user:
            raise ValueError(f"用户不存在: ID={user_id}")

        return list(getattr(user, 'roles', []) or [])
