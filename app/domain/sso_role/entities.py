"""SSO 角色域 - 领域模型

SSORole (SSO 角色定义)
UserSSORole (用户-SSO角色关联)

SSO 角色用于同步给外部系统，与系统内部的 auth 角色（admin/user/external）
和 permission 权限体系相互独立。外部系统通过 OAuth2 /userinfo 端点获取
用户的 SSO 角色列表，据此在自身系统中做权限判断。
"""

from typing import Optional, List

from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from yweb.orm import BaseModel

from app.domain.auth.model.user import User


class SSORole(BaseModel):
    """SSO 角色定义

    每条记录代表一个可分配给用户的 SSO 角色。
    SSO 角色会通过 OAuth2 userinfo 端点同步给外部系统。

    字段说明:
        - code: 角色编码（唯一），供外部系统识别，如 "finance_admin"
        - name: 角色显示名称，如 "财务管理员"
        - description: 角色描述
        - is_active: 是否启用
        - sort_order: 排序序号
    """
    __tablename__ = "sso_role"

    code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="角色编码（唯一），供外部系统识别",
    )
    # name 继承自 BaseModel
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="角色描述",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, server_default="1",
        comment="是否启用",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default="0",
        comment="排序序号",
    )

    def __repr__(self) -> str:
        return f"<SSORole(code='{self.code}', name='{self.name}')>"

    # ==================== 便捷查询 ====================

    @classmethod
    def get_by_code(cls, code: str) -> Optional["SSORole"]:
        """根据编码获取 SSO 角色"""
        return cls.query.filter_by(code=code).first()

    @classmethod
    def list_active(cls) -> List["SSORole"]:
        """获取所有启用的 SSO 角色（按 sort_order 排序）"""
        return cls.query.filter_by(is_active=True).order_by(cls.sort_order).all()

    @classmethod
    def list_all(cls) -> List["SSORole"]:
        """获取所有 SSO 角色（按 sort_order 排序）"""
        return cls.query.order_by(cls.sort_order).all()

    # ==================== 业务验证 ====================

    @classmethod
    def validate_code_unique(cls, code: str, exclude_id: int = None) -> None:
        """验证编码唯一性"""
        query = cls.query.filter_by(code=code)
        if exclude_id:
            query = query.filter(cls.id != exclude_id)
        if query.first():
            raise ValueError(f"SSO 角色编码已存在: {code}")


class UserSSORole(BaseModel):
    """用户-SSO角色关联

    多对多关系：一个用户可拥有多个 SSO 角色，一个 SSO 角色可分配给多个用户。
    """
    __tablename__ = "user_sso_role"
    __table_args__ = (
        UniqueConstraint('user_id', 'sso_role_id', name='uq_user_sso_role'),
    )

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False, index=True,
        comment="用户ID",
    )
    sso_role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sso_role.id"), nullable=False, index=True,
        comment="SSO角色ID",
    )

    def __repr__(self) -> str:
        return f"<UserSSORole(user_id={self.user_id}, sso_role_id={self.sso_role_id})>"

    # ==================== 便捷查询 ====================

    @classmethod
    def get_user_sso_role_codes(cls, user_id: int) -> List[str]:
        """获取用户的所有 SSO 角色编码"""
        rows = (
            cls.query
            .join(SSORole, cls.sso_role_id == SSORole.id)
            .filter(cls.user_id == user_id, SSORole.is_active == True)
            .with_entities(SSORole.code)
            .all()
        )
        return [r[0] for r in rows]

    @classmethod
    def get_users_by_sso_role(cls, sso_role_id: int) -> List[int]:
        """获取拥有指定 SSO 角色的所有用户 ID"""
        rows = (
            cls.query
            .filter_by(sso_role_id=sso_role_id)
            .with_entities(cls.user_id)
            .all()
        )
        return [r[0] for r in rows]

    @classmethod
    def assign(cls, user_id: int, sso_role_id: int) -> "UserSSORole":
        """分配 SSO 角色给用户"""
        existing = cls.query.filter_by(
            user_id=user_id, sso_role_id=sso_role_id
        ).first()
        if existing:
            raise ValueError("用户已拥有该 SSO 角色")

        rel = cls(user_id=user_id, sso_role_id=sso_role_id)
        rel.save(commit=True)
        return rel

    @classmethod
    def unassign(cls, user_id: int, sso_role_id: int) -> None:
        """移除用户的 SSO 角色"""
        rel = cls.query.filter_by(
            user_id=user_id, sso_role_id=sso_role_id
        ).first()
        if not rel:
            raise ValueError("用户未拥有该 SSO 角色")

        rel.delete(commit=True)
