"""SSO 角色域 - 服务层

提供 SSO 角色 CRUD 和用户 SSO 角色分配的业务逻辑。
"""

from typing import List, Optional

from yweb.log import get_logger
from yweb.orm import transaction_manager as tm

from .entities import SSORole, UserSSORole

logger = get_logger()


class SSORoleService:
    """SSO 角色管理服务

    处理 SSO 角色 CRUD 和用户 SSO 角色分配：
    - SSO 角色创建、更新、删除
    - 用户 SSO 角色分配、移除
    - 查询用户的 SSO 角色列表
    """

    # ==================== SSO 角色 CRUD ====================

    def list_roles(self, active_only: bool = False) -> List[SSORole]:
        """获取 SSO 角色列表"""
        if active_only:
            return SSORole.list_active()
        return SSORole.list_all()

    def get_role(self, code: str) -> SSORole:
        """根据编码获取 SSO 角色

        Raises:
            ValueError: 角色不存在
        """
        role = SSORole.get_by_code(code)
        if not role:
            raise ValueError(f"SSO 角色不存在: {code}")
        return role

    def get_role_by_id(self, role_id: int) -> SSORole:
        """根据 ID 获取 SSO 角色

        Raises:
            ValueError: 角色不存在
        """
        role = SSORole.get(role_id)
        if not role:
            raise ValueError(f"SSO 角色不存在: ID={role_id}")
        return role

    def create_role(
        self,
        code: str,
        name: str,
        description: str = None,
        sort_order: int = 0,
    ) -> SSORole:
        """创建 SSO 角色

        Raises:
            ValueError: 编码已存在
        """
        SSORole.validate_code_unique(code)

        role = SSORole(
            code=code,
            name=name,
            description=description,
            sort_order=sort_order,
            is_active=True,
        )
        role.save(commit=True)

        logger.info(f"SSO 角色创建成功: {role.code} ({role.name})")
        return role

    def update_role(self, code: str, **kwargs) -> SSORole:
        """更新 SSO 角色

        Raises:
            ValueError: 角色不存在 / 编码已存在
        """
        role = self.get_role(code)

        # 如果更新编码，验证唯一性
        if 'code' in kwargs and kwargs['code'] != role.code:
            SSORole.validate_code_unique(kwargs['code'], exclude_id=role.id)

        for key, value in kwargs.items():
            setattr(role, key, value)
        role.save(commit=True)

        logger.info(f"SSO 角色更新成功: {role.code}")
        return role

    def delete_role(self, code: str) -> None:
        """删除 SSO 角色（软删除）

        Raises:
            ValueError: 角色不存在
        """
        role = self.get_role(code)
        role.soft_delete()
        role.save(commit=True)
        logger.info(f"SSO 角色已删除: {role.code}")

    # ==================== 用户 SSO 角色管理 ====================

    def get_user_sso_roles(self, user_id: int) -> List[SSORole]:
        """获取用户的所有 SSO 角色（返回完整角色对象）"""
        role_ids = (
            UserSSORole.query
            .filter_by(user_id=user_id)
            .with_entities(UserSSORole.sso_role_id)
            .all()
        )
        if not role_ids:
            return []

        ids = [r[0] for r in role_ids]
        return SSORole.query.filter(
            SSORole.id.in_(ids),
            SSORole.is_active == True,
        ).order_by(SSORole.sort_order).all()

    def get_user_sso_role_codes(self, user_id: int) -> List[str]:
        """获取用户的 SSO 角色编码列表（轻量查询）"""
        return UserSSORole.get_user_sso_role_codes(user_id)

    def assign_role(self, user_id: int, sso_role_code: str) -> None:
        """给用户分配 SSO 角色

        Raises:
            ValueError: 角色不存在 / 用户已拥有该角色
        """
        role = self.get_role(sso_role_code)
        if not role.is_active:
            raise ValueError(f"SSO 角色已禁用: {sso_role_code}")

        UserSSORole.assign(user_id=user_id, sso_role_id=role.id)
        logger.info(f"SSO 角色分配成功: user_id={user_id}, role={sso_role_code}")

    def unassign_role(self, user_id: int, sso_role_code: str) -> None:
        """移除用户的 SSO 角色

        Raises:
            ValueError: 角色不存在 / 用户未拥有该角色
        """
        role = self.get_role(sso_role_code)
        UserSSORole.unassign(user_id=user_id, sso_role_id=role.id)
        logger.info(f"SSO 角色移除成功: user_id={user_id}, role={sso_role_code}")

    @tm.transactional()
    def set_user_sso_roles(self, user_id: int, sso_role_codes: List[str]) -> None:
        """全量设置用户的 SSO 角色（先清后加）

        Raises:
            ValueError: 角色编码不存在
        """
        # 删除旧的
        UserSSORole.query.filter_by(user_id=user_id).delete()

        # 添加新的
        for code in sso_role_codes:
            role = SSORole.get_by_code(code)
            if not role:
                raise ValueError(f"SSO 角色不存在: {code}")
            if not role.is_active:
                raise ValueError(f"SSO 角色已禁用: {code}")
            rel = UserSSORole(user_id=user_id, sso_role_id=role.id)
            rel.save()

        logger.info(
            f"SSO 角色全量设置: user_id={user_id}, roles={sso_role_codes}"
        )

    def list_role_users(self, sso_role_code: str) -> List[int]:
        """获取拥有指定 SSO 角色的所有用户 ID

        Raises:
            ValueError: 角色不存在
        """
        role = self.get_role(sso_role_code)
        return UserSSORole.get_users_by_sso_role(role.id)
