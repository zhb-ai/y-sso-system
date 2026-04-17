"""应用域 - 服务层

具体服务类，使用 Active Record 模式直接操作领域模型。
- ApplicationService: 应用管理（注册、配置、凭证管理）
- OAuth2TokenService: OAuth2 令牌管理（创建、验证、刷新、撤销）
"""

import json
import secrets
from typing import Optional, List
from datetime import datetime, timezone, timedelta

from jose import JWTError, jwt
from yweb.log import get_logger
from yweb.auth.schemas import TokenData, TokenPayload
from yweb.orm import transaction_manager as tm
from .entities import Application, ApplicationPermission, OAuth2Token, AuthorizationCode
from app.config import settings
from app.services.oauth2_security import (
    build_pkce_s256_challenge,
    get_jwt_key_id,
    get_runtime_jwt_public_key,
    get_oidc_issuer,
)

logger = get_logger()


class ApplicationService:
    """应用管理服务

    处理 SSO 客户端应用的生命周期管理：
    - 应用注册、更新、删除
    - 客户端凭证管理
    - 应用启用/禁用
    """

    @tm.transactional()
    def create_application(
        self,
        name: str,
        code: str,
        description: str = None,
        redirect_uris: List[str] = None,
        allowed_ip_cidrs: List[str] = None,
        logo_url: str = None,
        client_type: str = "confidential",
    ) -> Application:
        """创建应用

        Args:
            name: 应用名称
            code: 应用编码（唯一）
            description: 应用描述
            redirect_uris: 重定向URI列表
            logo_url: Logo URL

        Returns:
            创建的应用实体

        Raises:
            ValueError: 编码已存在
        """
        # 验证编码唯一性
        Application.validate_code_unique(code)
        normalized_ip_cidrs = Application.normalize_allowed_ip_cidrs(allowed_ip_cidrs)

        # 生成客户端凭证
        client_id, client_secret = Application.generate_client_credentials()
        if client_type == "public":
            client_secret = ""

        # 创建应用
        app = Application(
            name=name,
            code=code,
            description=description,
            client_id=client_id,
            client_secret=client_secret,
            client_type=client_type,
            redirect_uris=json.dumps(redirect_uris or []),
            allowed_ip_cidrs=json.dumps(normalized_ip_cidrs),
            logo_url=logo_url,
            is_active=True,
        )
        app.save()

        logger.info(f"创建应用: {name} (code={code}, client_id={client_id})")
        return app

    def get_application(self, app_id: int) -> Application:
        """获取应用

        Raises:
            ValueError: 应用不存在
        """
        app = Application.get(app_id)
        if not app:
            raise ValueError(f"应用不存在: {app_id}")
        return app

    def get_application_secret(self, app_id: int) -> Application:
        """获取应用当前客户端密钥

        Raises:
            ValueError: 应用不存在
        """
        return self.get_application(app_id)

    def get_application_by_client_id(self, client_id: str) -> Application:
        """通过客户端ID获取应用

        Raises:
            ValueError: 应用不存在
        """
        app = Application.query.filter_by(client_id=client_id).first()
        if not app:
            raise ValueError(f"客户端不存在: {client_id}")
        return app

    @tm.transactional()
    def update_application(self, app_id: int, **kwargs) -> Application:
        """更新应用

        Raises:
            ValueError: 应用不存在 / 编码已存在
        """
        app = self.get_application(app_id)

        # 如果更新编码，验证唯一性
        if 'code' in kwargs and kwargs['code'] != app.code:
            Application.validate_code_unique(kwargs['code'], exclude_id=app_id)

        # 处理 redirect_uris：List -> JSON string
        if 'redirect_uris' in kwargs and isinstance(kwargs['redirect_uris'], list):
            kwargs['redirect_uris'] = json.dumps(kwargs['redirect_uris'])

        # 处理 allowed_ip_cidrs：List -> JSON string
        if 'allowed_ip_cidrs' in kwargs and isinstance(kwargs['allowed_ip_cidrs'], list):
            kwargs['allowed_ip_cidrs'] = json.dumps(
                Application.normalize_allowed_ip_cidrs(kwargs['allowed_ip_cidrs'])
            )

        # 切换客户端类型时，同步维护客户端密钥状态
        new_client_type = kwargs.get('client_type')
        if new_client_type and new_client_type != app.client_type:
            if new_client_type == "public":
                kwargs['client_secret'] = ""
            elif new_client_type == "confidential":
                current_secret = kwargs.get('client_secret', app.client_secret)
                if not current_secret:
                    _, kwargs['client_secret'] = Application.generate_client_credentials()

        app.update(**kwargs)
        app.save()

        logger.info(f"更新应用: {app.name} (id={app_id})")
        return app

    def delete_application(self, app_id: int) -> None:
        """删除应用（软删除）

        Raises:
            ValueError: 应用不存在
        """
        app = self.get_application(app_id)
        app_name = app.name  # 在 commit 前获取 name
        app.soft_delete()
        app.save(commit=True)
        logger.info(f"删除应用: {app_name} (id={app_id})")

    def list_applications(
        self,
        keyword: str = None,
        is_active: bool = None,
        page: int = 1,
        page_size: int = 10,
    ):
        """分页查询应用列表

        Returns:
            分页结果对象
        """
        query = Application.query.order_by(Application.created_at.desc())

        if keyword:
            query = query.filter(
                Application.name.ilike(f"%{keyword}%") |
                Application.code.ilike(f"%{keyword}%")
            )

        if is_active is not None:
            query = query.filter(Application.is_active == is_active)

        return query.paginate(page=page, page_size=page_size)

    def reset_client_secret(self, app_id: int) -> tuple:
        """重置客户端密钥

        Returns:
            (application, new_secret) 元组

        Raises:
            ValueError: 应用不存在
        """
        app = self.get_application(app_id)
        if app.is_public_client():
            app.client_secret = ""
            app.save(commit=True)
            logger.info(f"公开客户端无需密钥: {app.name} (id={app_id})")
            return app, ""

        new_secret = secrets.token_urlsafe(48)
        app.client_secret = new_secret
        app.save(commit=True)

        logger.info(f"重置客户端密钥: {app.name} (id={app_id})")
        return app, new_secret

    def enable_application(self, app_id: int) -> Application:
        """启用应用

        Raises:
            ValueError: 应用不存在
        """
        app = self.get_application(app_id)
        app.is_active = True
        app.save(commit=True)
        logger.info(f"启用应用: {app.name} (id={app_id})")
        return app

    def disable_application(self, app_id: int) -> Application:
        """禁用应用

        Raises:
            ValueError: 应用不存在
        """
        app = self.get_application(app_id)
        app.is_active = False
        app.save(commit=True)
        logger.info(f"禁用应用: {app.name} (id={app_id})")
        return app

    def validate_client_credentials(
        self,
        client_id: str,
        client_secret: Optional[str],
        source_ip: Optional[str] = None,
    ) -> Application:
        """验证客户端凭证

        Raises:
            ValueError: 凭证无效 / 应用未激活
        """
        app = self.get_application_by_client_id(client_id)
        app.validate_is_active()
        app.validate_source_ip(source_ip)

        if app.is_public_client():
            return app

        if not client_secret:
            raise ValueError("缺少客户端凭证")

        if app.client_secret != client_secret:
            raise ValueError("客户端密钥错误")

        return app


class OAuth2TokenService:
    """OAuth2令牌服务

    处理 OAuth2 令牌的创建、验证、刷新和撤销。
    """

    def __init__(self, app_service: ApplicationService = None):
        self.app_service = app_service or ApplicationService()

    @tm.transactional()
    def create_token(
        self,
        application_id: int,
        user_id: int,
        expires_minutes: int = 30,
    ) -> OAuth2Token:
        """创建 OAuth2 令牌

        Returns:
            创建的令牌实体
        """
        access_token = secrets.token_urlsafe(64)
        refresh_token = secrets.token_urlsafe(64)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)

        token = OAuth2Token(
            application_id=application_id,
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        token.save()

        return token

    def validate_access_token(self, access_token: str) -> OAuth2Token:
        """验证访问令牌

        Raises:
            ValueError: 令牌无效 / 已过期
        """
        token = OAuth2Token.query.filter_by(access_token=access_token).first()
        if not token:
            raise ValueError("访问令牌无效")

        if token.is_expired():
            raise ValueError("访问令牌已过期")

        return token

    @tm.transactional()
    def refresh_token(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        expires_minutes: int = 30,
    ) -> OAuth2Token:
        """刷新访问令牌

        Raises:
            ValueError: 凭证无效 / 刷新令牌无效
        """
        # 验证客户端凭证
        app = self.app_service.validate_client_credentials(client_id, client_secret)

        # 查找刷新令牌
        old_token = OAuth2Token.query.filter_by(refresh_token=refresh_token).first()
        if not old_token:
            raise ValueError("刷新令牌无效")

        if old_token.application_id != app.id:
            raise ValueError("刷新令牌与客户端不匹配")

        # 更新访问令牌和过期时间
        old_token.access_token = secrets.token_urlsafe(64)
        old_token.expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=expires_minutes
        )
        old_token.save()

        return old_token

    def revoke_token(self, access_token: str) -> None:
        """撤销令牌（软删除）"""
        token = OAuth2Token.query.filter_by(access_token=access_token).first()
        if token:
            token.soft_delete()
            token.save(commit=True)

    def revoke_user_tokens(
        self, user_id: int, application_id: int = None
    ) -> None:
        """撤销用户的令牌"""
        query = OAuth2Token.query.filter_by(user_id=user_id)
        if application_id:
            query = query.filter_by(application_id=application_id)

        tokens = query.all()
        for token in tokens:
            token.soft_delete()

        if tokens:
            tokens[-1].save(commit=True)

    def get_user_tokens(self, user_id: int) -> List[OAuth2Token]:
        """获取用户的所有有效令牌"""
        return OAuth2Token.query.filter_by(user_id=user_id).all()


class OAuth2ProviderService:
    """OAuth2 授权服务器 服务

    作为 SSO 的 OAuth2 Provider，处理授权码流程：
    1. authorize  — 验证客户端、生成授权码
    2. token      — 用授权码换取 access_token / refresh_token
    3. userinfo   — 用 access_token 获取用户信息
    """

    def __init__(self, jwt_manager, user_getter):
        """
        Args:
            jwt_manager: JWTManager 实例（来自 auth.jwt_manager）
            user_getter: 用户获取函数 (user_id) -> User 或 None
        """
        self.jwt_manager = jwt_manager
        self.user_getter = user_getter
        self.app_service = ApplicationService()

    @staticmethod
    def _extract_roles(user) -> List[str]:
        """提取用户角色编码列表"""
        if not hasattr(user, "roles"):
            return []
        return [r.code if hasattr(r, "code") else str(r) for r in user.roles]

    def _build_token_payload(self, user, client_id: str) -> TokenPayload:
        """构造 access/refresh token 共用载荷"""
        return TokenPayload(
            sub=str(user.id),
            user_id=user.id,
            username=user.username,
            email=getattr(user, "email", None),
            roles=self._extract_roles(user),
            extra={
                "iss": get_oidc_issuer(),
                "aud": client_id,
            },
        )

    def _create_id_token(self, user, client_id: str, nonce: Optional[str] = None) -> str:
        """创建 OIDC id_token"""
        now = datetime.now(timezone.utc)
        claims = {
            "sub": str(user.id),
            "iss": get_oidc_issuer(),
            "aud": client_id,
            "iat": now,
            "exp": now + timedelta(minutes=self.jwt_manager.access_token_expire_minutes),
            "name": getattr(user, "name", None) or user.username,
            "email": getattr(user, "email", None),
            "preferred_username": user.username,
        }
        if nonce:
            claims["nonce"] = nonce
        return jwt.encode(
            claims,
            self.jwt_manager.secret_key,
            algorithm=self.jwt_manager.algorithm,
            headers={"kid": get_jwt_key_id()},
        )

    @staticmethod
    def _scope_contains_openid(scope: Optional[str]) -> bool:
        """判断 scope 是否包含 openid"""
        return "openid" in (scope or "").split()

    def _load_active_user(self, user_id: int):
        """优先用当前会话查询用户，必要时回退到注入的 user_getter"""
        from app.domain.auth.model.user import User

        try:
            user = User.query.filter_by(id=user_id, is_active=True).first()
            if user:
                return user
        except Exception:
            user = None

        if self.user_getter:
            user = self.user_getter(user_id)
            if user and (not hasattr(user, "is_active") or user.is_active):
                return user
        return None

    def _decode_resource_access_token_payload(self, access_token: str) -> Optional[dict]:
        """解码资源端点使用的 access token payload。"""
        verification_key = get_runtime_jwt_public_key() or self.jwt_manager.secret_key
        try:
            return jwt.decode(
                access_token,
                verification_key,
                algorithms=[self.jwt_manager.algorithm],
                issuer=get_oidc_issuer(),
                options={"verify_aud": False},
            )
        except JWTError:
            return None
        except Exception:
            return None

    @staticmethod
    def _extract_client_id_from_payload(payload: Optional[dict]) -> Optional[str]:
        """从 token payload 中提取客户端 ID。"""
        if not payload:
            return None

        audience = payload.get("aud")
        if isinstance(audience, str):
            return audience
        if isinstance(audience, list) and audience:
            return str(audience[0])
        return None

    def _verify_resource_access_token(self, access_token: str) -> Optional[TokenData]:
        """校验提供给 userinfo 这类资源端点的 access token。"""
        payload = self._decode_resource_access_token_payload(access_token)
        if not payload:
            return None

        return TokenData(
            sub=payload.get("sub"),
            user_id=payload.get("user_id"),
            username=payload.get("username"),
            email=payload.get("email"),
            roles=payload.get("roles", []),
            token_type=payload.get("token_type", "access"),
            exp=payload.get("exp"),
            iat=payload.get("iat"),
        )

    def validate_authorize_request(
        self,
        client_id: str,
        redirect_uri: str,
        response_type: str = "code",
        code_challenge: str = None,
        code_challenge_method: str = None,
    ) -> Application:
        """验证授权请求参数

        Returns:
            Application 实体

        Raises:
            ValueError: 客户端不存在 / 重定向URI无效 / response_type 不支持
        """
        if response_type != "code":
            raise ValueError("仅支持 response_type=code")

        app = self.app_service.get_application_by_client_id(client_id)
        app.validate_is_active()
        app.validate_redirect_uri(redirect_uri)

        if app.is_public_client():
            if not code_challenge:
                raise ValueError("公开客户端必须提供 code_challenge")
            if code_challenge_method != "S256":
                raise ValueError("公开客户端仅支持 code_challenge_method=S256")

        if code_challenge and code_challenge_method != "S256":
            raise ValueError("当前仅支持 code_challenge_method=S256")

        return app

    @tm.transactional()
    def create_authorization_code(
        self,
        application_id: int,
        user_id: int,
        redirect_uri: str,
        scope: str = None,
        state: str = None,
        nonce: str = None,
        code_challenge: str = None,
        code_challenge_method: str = None,
    ) -> AuthorizationCode:
        """生成授权码

        Returns:
            AuthorizationCode 实体
        """
        auth_code = AuthorizationCode.create_code(
            application_id=application_id,
            user_id=user_id,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            nonce=nonce,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
        logger.info(
            f"生成授权码: app_id={application_id}, user_id={user_id}, "
            f"code={auth_code.code[:8]}..."
        )
        return auth_code

    @tm.transactional()
    def exchange_code_for_token(
        self,
        code: str,
        client_id: str,
        client_secret: Optional[str],
        redirect_uri: str,
        code_verifier: str = None,
        source_ip: Optional[str] = None,
    ) -> dict:
        """用授权码换取令牌

        Args:
            code: 授权码
            client_id: 客户端 ID
            client_secret: 客户端密钥
            redirect_uri: 重定向URI（必须与授权时一致）

        Returns:
            {"access_token": ..., "token_type": "bearer", "expires_in": ...,
             "refresh_token": ..., "scope": ...}

        Raises:
            ValueError: 凭证无效 / 授权码无效
        """
        # 1. 验证客户端凭证与来源 IP
        app = self.app_service.validate_client_credentials(
            client_id,
            client_secret,
            source_ip=source_ip,
        )

        # 2. 查找授权码
        auth_code = AuthorizationCode.query.filter_by(code=code).first()
        if not auth_code:
            raise ValueError("授权码无效")

        # 3. 验证授权码可用
        auth_code.validate_usable()

        # 4. 验证授权码属于该客户端
        if auth_code.application_id != app.id:
            raise ValueError("授权码与客户端不匹配")

        # 5. 验证 redirect_uri 一致
        if auth_code.redirect_uri != redirect_uri:
            raise ValueError("redirect_uri 不匹配")

        # 6. 验证客户端认证 / PKCE
        if app.is_public_client():
            self._validate_pkce(auth_code, code_verifier)
        else:
            if getattr(auth_code, "code_challenge", None):
                self._validate_pkce(auth_code, code_verifier)

        # 7. 标记授权码为已使用
        auth_code.mark_used()

        # 8. 获取用户信息并创建 JWT
        #    直接在当前事务 Session 内查询，避免 user_getter 返回 detached 实例
        #    导致 lazy load roles 失败
        user = self._load_active_user(auth_code.user_id)
        if not user:
            raise ValueError("用户不存在或已禁用")

        payload = self._build_token_payload(user, client_id)

        access_token = self.jwt_manager.create_access_token(payload)
        refresh_token = self.jwt_manager.create_refresh_token(payload)

        expires_in = self.jwt_manager.access_token_expire_minutes * 60

        logger.info(
            f"授权码换取令牌: app={app.name}, user={user.username}"
        )

        response = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "refresh_token": refresh_token,
            "scope": auth_code.scope or "",
        }
        if self._scope_contains_openid(auth_code.scope):
            nonce = getattr(auth_code, "nonce", None)
            if not isinstance(nonce, str) or not nonce:
                nonce = None
            response["id_token"] = self._create_id_token(
                user,
                client_id,
                nonce=nonce,
            )
        return response

    @tm.transactional()
    def refresh_access_token(
        self,
        refresh_token: str,
        client_id: str,
        client_secret: Optional[str],
        source_ip: Optional[str] = None,
    ) -> dict:
        """用 refresh_token 换取新的 access_token

        Raises:
            ValueError: 凭证无效 / refresh_token 无效
        """
        # 验证客户端凭证
        self.app_service.validate_client_credentials(
            client_id,
            client_secret,
            source_ip=source_ip,
        )

        token_data = self.jwt_manager.verify_token(refresh_token)
        if not token_data or not token_data.user_id or token_data.token_type != "refresh":
            raise ValueError("refresh_token 无效或已过期")

        user = self._load_active_user(token_data.user_id)
        if not user:
            raise ValueError("用户不存在或已禁用")

        payload = self._build_token_payload(user, client_id)
        response = {
            "access_token": self.jwt_manager.create_access_token(payload),
            "token_type": "bearer",
            "expires_in": self.jwt_manager.access_token_expire_minutes * 60,
        }

        # 如果触发了滑动过期，返回新的 refresh_token
        if self.jwt_manager.should_renew_refresh_token(refresh_token):
            response["refresh_token"] = self.jwt_manager.create_refresh_token(payload)

        response["id_token"] = self._create_id_token(user, client_id)
        return response

    @staticmethod
    def _validate_pkce(auth_code: AuthorizationCode, code_verifier: Optional[str]) -> None:
        """验证 PKCE"""
        if not getattr(auth_code, "code_challenge", None):
            raise ValueError("公开客户端授权码缺少 PKCE challenge")

        if not code_verifier:
            raise ValueError("缺少 code_verifier")

        method = getattr(auth_code, "code_challenge_method", None) or "plain"
        if method != "S256":
            raise ValueError(f"不支持的 code_challenge_method: {method}")

        expected = build_pkce_s256_challenge(code_verifier)
        if expected != auth_code.code_challenge:
            raise ValueError("code_verifier 验证失败")

    def get_userinfo(self, access_token: str, source_ip: Optional[str] = None) -> dict:
        """通过 access_token 获取用户信息

        Args:
            access_token: JWT access_token

        Returns:
            用户信息字典（符合 OIDC UserInfo 规范）

        Raises:
            ValueError: token 无效或已过期
        """
        payload = self._decode_resource_access_token_payload(access_token)
        if not payload:
            raise ValueError("access_token 无效或已过期")

        token_data = TokenData(
            sub=payload.get("sub"),
            user_id=payload.get("user_id"),
            username=payload.get("username"),
            email=payload.get("email"),
            roles=payload.get("roles", []),
            token_type=payload.get("token_type", "access"),
            exp=payload.get("exp"),
            iat=payload.get("iat"),
        )
        if token_data.token_type != "access":
            raise ValueError("无效的令牌类型")

        client_id = self._extract_client_id_from_payload(payload)
        if client_id:
            app = self.app_service.get_application_by_client_id(client_id)
            app.validate_is_active()
            app.validate_source_ip(source_ip)

        from app.domain.auth.model.user import User
        user = User.query.filter_by(id=token_data.user_id, is_active=True).first()
        if not user:
            raise ValueError("用户不存在或已禁用")

        # 构造符合 OIDC 标准的 userinfo 响应
        userinfo = {
            "sub": str(user.id),
            "preferred_username": user.username,
            "name": getattr(user, 'display_name', user.username),
            "email": getattr(user, 'email', None),
            "phone_number": getattr(user, 'phone', None),
            "active": getattr(user, 'is_active', True),
        }

        # 系统内部角色
        if hasattr(user, 'roles'):
            userinfo["roles"] = [
                r.code if hasattr(r, 'code') else str(r) for r in user.roles
            ]

        # SSO 角色（供外部系统使用）
        from app.domain.sso_role.entities import UserSSORole
        userinfo["sso_roles"] = UserSSORole.get_user_sso_role_codes(user.id)

        # 关联员工编码（供 SSO 下游如 Superset 等使用）
        try:
            from app.models_registry import get_app_org_models
            org_models = get_app_org_models()
            if org_models is not None:
                employee_cls = org_models.Employee
                employee = employee_cls.query.filter(employee_cls.user_id == user.id).first()
                if employee is not None and getattr(employee, "code", None) is not None:
                    userinfo["user_code"] = getattr(employee, "code", None)
        except Exception as e:
            logger.debug("get_userinfo: 解析员工编码跳过, %s", e)

        return userinfo
