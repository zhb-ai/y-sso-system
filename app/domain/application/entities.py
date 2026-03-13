"""应用域 - 领域模型

Application (SSO 客户端应用)
├── ApplicationPermission (应用-角色权限)
├── OAuth2Token (OAuth2 令牌)
└── AuthorizationCode (OAuth2 授权码)

使用 Active Record + DDD 思想：
- 领域模型继承 BaseModel，具备数据访问能力
- 业务规则封装在 validate_xxx() 方法中
- 关系使用 fields.* API，支持级联软删除
"""

import json
import secrets
from typing import Optional, List
from datetime import datetime, timezone, timedelta

from sqlalchemy import Text, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from yweb.orm import BaseModel, fields

from app.domain.auth.model.user import User


class Application(BaseModel):
    """应用实体 - SSO 客户端应用

    富领域模型：包含数据字段和业务验证方法。
    使用 Active Record 模式，继承 BaseModel 获得数据访问能力。
    """
    __tablename__ = "application"

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="应用名称"
    )
    code: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, comment="应用编码"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="应用描述"
    )
    client_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, comment="客户端ID"
    )
    client_secret: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="客户端密钥"
    )
    redirect_uris: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="重定向URI列表（JSON格式存储）"
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Logo图片URL"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否激活"
    )

    # ==================== 业务验证方法 ====================

    @classmethod
    def validate_code_unique(cls, code: str, exclude_id: int = None) -> None:
        """验证应用编码唯一"""
        if not code:
            return
        query = cls.query.filter_by(code=code)
        if exclude_id:
            query = query.filter(cls.id != exclude_id)
        if query.first():
            raise ValueError(f"应用编码已存在: {code}")

    @classmethod
    def validate_client_id_unique(cls, client_id: str, exclude_id: int = None) -> None:
        """验证客户端ID唯一"""
        if not client_id:
            return
        query = cls.query.filter_by(client_id=client_id)
        if exclude_id:
            query = query.filter(cls.id != exclude_id)
        if query.first():
            raise ValueError(f"客户端ID已存在: {client_id}")

    def validate_is_active(self) -> None:
        """验证应用是否为激活状态"""
        if not self.is_active:
            raise ValueError(f"应用已禁用: {self.name}")

    def validate_redirect_uri(self, uri: str) -> None:
        """验证重定向URI是否有效"""
        if uri not in self.get_redirect_uris():
            raise ValueError(f"重定向URI无效: {uri}")

    # ==================== 业务方法 ====================

    @staticmethod
    def generate_client_credentials() -> tuple:
        """生成客户端凭证 (client_id, client_secret)"""
        client_id = secrets.token_urlsafe(32)
        client_secret = secrets.token_urlsafe(48)
        return client_id, client_secret

    def add_redirect_uri(self, uri: str) -> None:
        """添加重定向URI"""
        uris = self.get_redirect_uris()
        if uri not in uris:
            uris.append(uri)
            self.redirect_uris = json.dumps(uris)

    def remove_redirect_uri(self, uri: str) -> None:
        """移除重定向URI"""
        uris = self.get_redirect_uris()
        if uri in uris:
            uris.remove(uri)
            self.redirect_uris = json.dumps(uris)

    def get_redirect_uris(self) -> List[str]:
        """获取重定向URI列表"""
        if self.redirect_uris:
            return json.loads(self.redirect_uris)
        return []


class ApplicationPermission(BaseModel):
    """应用权限实体 - 应用与角色的关联"""
    __tablename__ = "application_permission"

    # 使用 fields.ManyToOne：应用删除时级联删除权限
    application = fields.ManyToOne(
        Application, on_delete=fields.DELETE, nullable=False
    )

    # Role 模型由框架 setup_auth() 动态创建，无法在导入时引用，使用传统 ForeignKey
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("role.id"), nullable=False, comment="角色ID"
    )

    # ==================== 业务验证方法 ====================

    @classmethod
    def validate_not_exists(cls, application_id: int, role_id: int) -> None:
        """验证应用权限不存在（防止重复）"""
        if cls.query.filter_by(application_id=application_id, role_id=role_id).first():
            raise ValueError(
                f"应用权限已存在: application_id={application_id}, role_id={role_id}"
            )


class OAuth2Token(BaseModel):
    """OAuth2令牌实体"""
    __tablename__ = "oauth2_token"

    # 使用 fields.ManyToOne：应用删除时级联删除令牌
    application = fields.ManyToOne(
        Application, on_delete=fields.DELETE, nullable=False
    )

    # 用户删除时级联删除令牌
    user = fields.ManyToOne(
        User, on_delete=fields.DELETE, nullable=False
    )

    access_token: Mapped[str] = mapped_column(
        String(500), nullable=False, unique=True, comment="访问令牌"
    )
    refresh_token: Mapped[str] = mapped_column(
        String(500), nullable=False, unique=True, comment="刷新令牌"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="过期时间"
    )

    # ==================== 业务方法 ====================

    def is_expired(self) -> bool:
        """检查令牌是否过期"""
        if self.expires_at is None:
            return True
        now = datetime.now(timezone.utc)
        # 确保 expires_at 是带时区的 datetime 对象
        if self.expires_at.tzinfo is None:
            expires_at = self.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = self.expires_at
        return now > expires_at


class AuthorizationCode(BaseModel):
    """OAuth2 授权码实体

    授权码流程中的临时凭证，用于换取 access_token。
    授权码具有短时效性（默认1分钟），使用一次后即失效。
    """
    __tablename__ = "authorization_code"

    code: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True, comment="授权码"
    )

    # 关联应用 —— 应用删除时级联删除授权码
    application = fields.ManyToOne(
        Application, on_delete=fields.DELETE, nullable=False
    )

    # 关联用户 —— 用户删除时级联删除授权码
    user = fields.ManyToOne(
        User, on_delete=fields.DELETE, nullable=False
    )

    redirect_uri: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="授权时使用的重定向URI"
    )
    scope: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="授权范围"
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="CSRF state 参数"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="过期时间"
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否已使用"
    )

    # ==================== 业务方法 ====================

    @classmethod
    def create_code(
        cls,
        application_id: int,
        user_id: int,
        redirect_uri: str,
        scope: str = None,
        state: str = None,
        expires_minutes: int = 5,
    ) -> "AuthorizationCode":
        """创建授权码"""
        code_value = secrets.token_urlsafe(32)
        auth_code = cls()
        auth_code.code = code_value
        auth_code.application_id = application_id
        auth_code.user_id = user_id
        auth_code.redirect_uri = redirect_uri
        auth_code.scope = scope
        auth_code.state = state
        auth_code.expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        auth_code.is_used = False
        auth_code.save(commit=True)
        return auth_code

    def is_expired(self) -> bool:
        """检查授权码是否过期"""
        if self.expires_at is None:
            return True
        now = datetime.now(timezone.utc)
        # 确保 expires_at 是带时区的 datetime 对象
        if self.expires_at.tzinfo is None:
            expires_at = self.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = self.expires_at
        return now > expires_at

    def mark_used(self) -> None:
        """标记授权码为已使用"""
        self.is_used = True
        self.save(commit=True)

    def validate_usable(self) -> None:
        """验证授权码可用（未过期、未使用）"""
        if self.is_used:
            raise ValueError("授权码已被使用")
        if self.is_expired():
            raise ValueError("授权码已过期")
