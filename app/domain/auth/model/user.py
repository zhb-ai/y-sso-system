from __future__ import annotations

from typing import Optional
from enum import Enum
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from yweb.auth import AbstractUser, LockableMixin


class UserRoleEnum(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"      # 管理员
    USER = "user"        # 内部员工
    EXTERNAL = "external" # 外部用户


class User(LockableMixin, AbstractUser):
    """用户模型
    
    继承 AbstractUser 获得认证核心字段：
        - username, password_hash, email, phone, is_active, last_login_at
        - get_by_username(), get_by_email(), get_by_phone(), update_last_login()
        - display_name 属性
    
    混入 LockableMixin 获得账户安全功能：
        - is_locked, locked_at, locked_until, lock_reason, failed_login_attempts
        - lock(), unlock(), can_login, record_failed_login(), reset_failed_attempts()
        - 框架自动检测并启用：失败累计 → 自动锁定 → 到期解锁 → 成功重置
    
    角色管理由 setup_auth(User, role_model=True) 自动设置：
        - User.roles: ManyToMany relationship
        - has_role(), has_any_role(), has_all_roles()
        - add_role(), remove_role(), role_codes
    
    在此基础上添加项目特有字段和业务方法。
    """
    
    # ==================== 项目特有字段 ====================
    
    wechat_user_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, index=True, nullable=True, comment="微信用户ID"
    )
    
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="0",
        comment="是否需要修改密码（首次登录强制修改）"
    )
    
    # ==================== 项目特有查询 ====================
    
    @classmethod
    def get_by_wechat_id(cls, wechat_user_id: str) -> Optional[User]:
        """通过微信用户ID获取用户"""
        return cls.query.filter(cls.wechat_user_id == wechat_user_id).first()
    
    @classmethod
    def create_with_role(
        cls,
        username: str,
        password_hash: str,
        email: str,
        role_enum: UserRoleEnum,
        phone: Optional[str] = None,
        name: Optional[str] = None,
    ) -> User:
        """创建用户并分配指定角色
        
        Args:
            username: 用户名
            password_hash: 密码哈希值
            email: 邮箱
            role_enum: 用户角色枚举值
            phone: 手机号（可选）
            name: 显示名称（可选，如员工姓名）
            
        Returns:
            创建的用户对象
        """
        from app.api.dependencies import auth
        Role = auth.role_model
        
        user = cls(
            username=username,
            password_hash=password_hash,
            email=email,
            phone=phone,
            name=name,
            is_active=True
        )
        user.add(True)
        
        # 通过 relationship 分配角色
        role = Role.get_by_code(role_enum.value)
        if role:
            user.add_role(role)
            user.save(True)
        
        return user
