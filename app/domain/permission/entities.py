"""权限域 - 领域模型

Permission (功能权限)
RolePermission (角色-权限关联)

轻量级权限模型，配合 yweb.auth 的 Role 使用。
权限粒度为模块级（如 application:*），不做操作级拆分。
"""

from typing import Optional, List

from sqlalchemy import String, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from yweb.orm import BaseModel, transaction_manager as tm


class Permission(BaseModel):
    """功能权限
    
    每条记录代表一个可分配的权限点。
    code 格式：module:action，如 application:manage, user:manage
    module 用于前端树形分组展示。
    """
    __tablename__ = "permission"
    
    code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="权限编码，如 application:manage",
    )
    # name 继承自 BaseModel（角色名称/显示名称）
    module: Mapped[str] = mapped_column(
        String(100), nullable=False, default="",
        comment="所属模块名称，用于树形分组，如 应用管理",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="权限描述",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="排序序号",
    )
    
    def __repr__(self) -> str:
        return f"<Permission(code='{self.code}', name='{self.name}')>"
    
    # ==================== 便捷查询 ====================
    
    @classmethod
    def get_by_code(cls, code: str) -> Optional["Permission"]:
        """根据权限编码获取"""
        return cls.query.filter_by(code=code).first()
    
    @classmethod
    def list_all(cls) -> List["Permission"]:
        """获取所有权限（按 module + sort_order 排序）"""
        return cls.query.order_by(cls.module, cls.sort_order).all()
    
    @classmethod
    def list_by_module(cls, module: str) -> List["Permission"]:
        """获取某模块下的所有权限"""
        return cls.query.filter_by(module=module).order_by(cls.sort_order).all()
    
    @classmethod
    def get_module_tree(cls) -> dict:
        """获取按模块分组的权限树
        
        Returns:
            { "应用管理": [Permission, ...], "用户管理": [...], ... }
        """
        perms = cls.list_all()
        tree = {}
        for p in perms:
            tree.setdefault(p.module, []).append(p)
        return tree


class RolePermission(BaseModel):
    """角色-权限关联
    
    多对多关系：一个角色可拥有多个权限，一个权限可被多个角色拥有。
    """
    __tablename__ = "role_permission"
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )
    
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("role.id"), nullable=False, index=True,
        comment="角色ID",
    )
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("permission.id"), nullable=False, index=True,
        comment="权限ID",
    )
    
    def __repr__(self) -> str:
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"
    
    # ==================== 便捷查询 ====================
    
    @classmethod
    def get_role_permission_codes(cls, role_id: int) -> set:
        """获取角色拥有的所有权限编码"""
        rows = (
            cls.query
            .join(Permission, cls.permission_id == Permission.id)
            .filter(cls.role_id == role_id)
            .with_entities(Permission.code)
            .all()
        )
        return {r[0] for r in rows}
    
    @classmethod
    @tm.transactional()
    def set_role_permissions(cls, role_id: int, permission_ids: List[int]) -> None:
        """全量设置角色权限（先清后加）
        
        使用 @transactional 装饰器，自动管理事务：
        - 函数正常返回时自动提交
        - 抛出异常时自动回滚
        """
        # 删除旧的
        cls.query.filter_by(role_id=role_id).delete()
        # 添加新的
        for pid in permission_ids:
            rp = cls(role_id=role_id, permission_id=pid)
            rp.save()
        # @transactional 自动提交，无需手动 commit
    
    @classmethod
    def get_permissions_by_role_ids(cls, role_ids: List[int]) -> set:
        """批量获取多个角色的权限编码合集"""
        if not role_ids:
            return set()
        rows = (
            cls.query
            .join(Permission, cls.permission_id == Permission.id)
            .filter(cls.role_id.in_(role_ids))
            .with_entities(Permission.code)
            .all()
        )
        return {r[0] for r in rows}
