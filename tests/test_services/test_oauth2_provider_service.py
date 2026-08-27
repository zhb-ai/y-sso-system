"""OAuth2 Provider Service 测试"""

import base64
import hashlib
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from jose import jwt

from app.config import settings
from app.domain.application.entities import Application, AuthorizationCode
from app.domain.application.services import OAuth2ProviderService
from app.domain.auth.model.user import User
from app.services.oauth2_security import build_runtime_jwt_settings
from yweb.auth import JWTManager
from yweb.orm import init_database


def _override_oidc_issuer(value: str):
    """覆盖 oidc_issuer，并返回恢复函数"""
    had_attr = hasattr(settings, "oidc_issuer")
    original = getattr(settings, "oidc_issuer", None)
    object.__setattr__(settings, "oidc_issuer", value)

    def _restore():
        if had_attr:
            object.__setattr__(settings, "oidc_issuer", original)
        else:
            object.__delattr__(settings, "oidc_issuer")

    return _restore


class QueryStub:
    """最小查询桩对象"""

    def __init__(self, result):
        self.result = result

    def filter_by(self, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result

    def all(self):
        return [self.result] if self.result is not None else []


class ListQueryStub:
    """返回固定列表的查询桩"""

    def __init__(self, items):
        self.items = list(items)

    def filter(self, *args, **kwargs):
        return self

    def filter_by(self, **kwargs):
        return self

    def first(self):
        return self.items[0] if self.items else None

    def all(self):
        return list(self.items)


def _stub_employee(monkeypatch, employee, org_rels=None, dept_rels=None, departments=None):
    """为 OAuth username / userinfo 组织字段打桩员工查询"""
    from app import models_registry

    dept_by_id = {dept.id: dept for dept in (departments or [])}

    class DepartmentModel:
        query = ListQueryStub(departments or [])

        @staticmethod
        def get(dept_id):
            return dept_by_id.get(dept_id)

    org_models = SimpleNamespace(
        Employee=SimpleNamespace(query=QueryStub(employee), user_id=object()),
        EmployeeOrgRel=SimpleNamespace(
            query=ListQueryStub(org_rels or []),
            employee_id=object(),
        ),
        EmployeeDeptRel=SimpleNamespace(
            query=ListQueryStub(dept_rels or []),
            employee_id=object(),
        ),
        Department=DepartmentModel,
    )
    monkeypatch.setattr(models_registry, "get_app_org_models", lambda: org_models)


class FakeJWTManager:
    """记录 TokenPayload 的最小 JWT 管理器"""

    access_token_expire_minutes = 30
    secret_key = "test-secret"
    algorithm = "HS256"

    def __init__(self):
        self.access_payload = None
        self.refresh_payload = None
        self.should_renew = True
        self.verify_result = SimpleNamespace(
            sub="7",
            user_id=7,
            token_type="refresh",
        )

    def create_access_token(self, payload):
        self.access_payload = payload
        return "access-token"

    def create_refresh_token(self, payload):
        self.refresh_payload = payload
        return "refresh-token"

    def verify_token(self, token):
        return self.verify_result

    def should_renew_refresh_token(self, refresh_token):
        return self.should_renew


def _build_s256_challenge(verifier: str) -> str:
    """生成 PKCE S256 challenge"""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


class TestOAuth2ProviderService:
    """OAuth2 Provider Service 行为测试"""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """初始化事务管理器所需的最小数据库环境"""
        engine, _ = init_database("sqlite:///:memory:")
        Application.__table__.create(bind=engine)
        User.__table__.create(bind=engine)
        AuthorizationCode.__table__.create(bind=engine)
        yield
        engine.dispose()

    def test_exchange_code_for_token_uses_user_id_as_sub(self, monkeypatch):
        """授权码换 token 时，JWT 的 sub 应统一为用户 ID 字符串"""
        jwt_manager = FakeJWTManager()
        service = OAuth2ProviderService(jwt_manager=jwt_manager, user_getter=lambda _: None)

        app_obj = SimpleNamespace(
            id=100,
            name="Data Formulator",
            client_type="confidential",
            validate_is_active=Mock(),
            is_public_client=lambda: False,
        )
        service.app_service.get_application_by_client_id = Mock(return_value=app_obj)
        service.app_service.validate_client_credentials = Mock(return_value=app_obj)

        auth_code = Mock(
            application_id=100,
            user_id=7,
            redirect_uri="http://localhost:5567/callback",
            scope="openid profile email",
            code_challenge=None,
            code_challenge_method=None,
        )
        auth_code.validate_usable = Mock()
        auth_code.mark_used = Mock()

        user = SimpleNamespace(
            id=7,
            username="zhanghaibin",
            email=None,
            roles=[SimpleNamespace(code="admin"), SimpleNamespace(code="user")],
        )

        monkeypatch.setattr(AuthorizationCode, "query", QueryStub(auth_code), raising=False)
        monkeypatch.setattr(User, "query", QueryStub(user), raising=False)
        _stub_employee(
            monkeypatch,
            SimpleNamespace(
                id=1,
                code="E001",
                enterprise_wechat_user_id="WeiXinZhang001",
            ),
        )

        result = service.exchange_code_for_token(
            code="test-code",
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="http://localhost:5567/callback",
        )

        assert result["access_token"] == "access-token"
        assert result["refresh_token"] == "refresh-token"
        assert jwt_manager.access_payload.sub == "7"
        assert jwt_manager.refresh_payload.sub == "7"
        assert jwt_manager.access_payload.username == "zhanghaibin"
        assert jwt_manager.refresh_payload.username == "zhanghaibin"

    def test_exchange_code_for_public_client_accepts_pkce_without_client_secret(self, monkeypatch):
        """公开客户端应允许通过 PKCE 换 token，而无需 client_secret"""
        jwt_manager = FakeJWTManager()
        service = OAuth2ProviderService(jwt_manager=jwt_manager, user_getter=lambda _: None)

        public_app = SimpleNamespace(
            id=100,
            name="Public App",
            client_type="public",
            validate_is_active=Mock(),
            validate_source_ip=Mock(),
            is_public_client=lambda: True,
        )
        service.app_service.get_application_by_client_id = Mock(return_value=public_app)
        service.app_service.validate_client_credentials = Mock(return_value=public_app)

        code_verifier = "pkce-verifier-1234567890"
        auth_code = Mock(
            application_id=100,
            user_id=7,
            redirect_uri="http://localhost:5567/callback",
            scope="openid profile email",
            code_challenge=_build_s256_challenge(code_verifier),
            code_challenge_method="S256",
        )
        auth_code.validate_usable = Mock()
        auth_code.mark_used = Mock()

        user = SimpleNamespace(
            id=7,
            username="zhanghaibin",
            email=None,
            roles=[SimpleNamespace(code="admin")],
        )

        monkeypatch.setattr(AuthorizationCode, "query", QueryStub(auth_code), raising=False)
        monkeypatch.setattr(User, "query", QueryStub(user), raising=False)

        result = service.exchange_code_for_token(
            code="test-code",
            client_id="public-client-id",
            client_secret=None,
            redirect_uri="http://localhost:5567/callback",
            code_verifier=code_verifier,
        )

        assert result["access_token"] == "access-token"
        assert result["refresh_token"] == "refresh-token"

    def test_exchange_code_for_public_client_requires_code_verifier(self, monkeypatch):
        """公开客户端缺少 code_verifier 时应拒绝换 token"""
        jwt_manager = FakeJWTManager()
        service = OAuth2ProviderService(jwt_manager=jwt_manager, user_getter=lambda _: None)

        public_app = SimpleNamespace(
            id=100,
            name="Public App",
            client_type="public",
            validate_is_active=Mock(),
            validate_source_ip=Mock(),
            is_public_client=lambda: True,
        )
        service.app_service.get_application_by_client_id = Mock(return_value=public_app)
        service.app_service.validate_client_credentials = Mock(return_value=public_app)

        auth_code = Mock(
            application_id=100,
            user_id=7,
            redirect_uri="http://localhost:5567/callback",
            scope="openid profile email",
            code_challenge="challenge",
            code_challenge_method="S256",
        )
        auth_code.validate_usable = Mock()
        auth_code.mark_used = Mock()

        monkeypatch.setattr(AuthorizationCode, "query", QueryStub(auth_code), raising=False)

        with pytest.raises(ValueError, match="code_verifier"):
            service.exchange_code_for_token(
                code="test-code",
                client_id="public-client-id",
                client_secret=None,
                redirect_uri="http://localhost:5567/callback",
                code_verifier=None,
            )

    def test_exchange_code_for_token_rejects_ip_outside_whitelist(self, monkeypatch):
        """授权码换 token 时应校验应用 IP 白名单"""
        jwt_manager = FakeJWTManager()
        service = OAuth2ProviderService(jwt_manager=jwt_manager, user_getter=lambda _: None)

        app_obj = SimpleNamespace(
            id=100,
            name="Data Formulator",
            client_type="confidential",
            validate_is_active=Mock(),
            validate_source_ip=Mock(),
            is_public_client=lambda: False,
        )
        service.app_service.validate_client_credentials = Mock(
            side_effect=ValueError("来源IP不在应用白名单内")
        )

        auth_code = Mock(
            application_id=100,
            user_id=7,
            redirect_uri="http://localhost:5567/callback",
            scope="openid profile email",
            code_challenge=None,
            code_challenge_method=None,
        )
        auth_code.validate_usable = Mock()
        auth_code.mark_used = Mock()

        monkeypatch.setattr(AuthorizationCode, "query", QueryStub(auth_code), raising=False)

        with pytest.raises(ValueError, match="白名单"):
            service.exchange_code_for_token(
                code="test-code",
                client_id="client-id",
                client_secret="client-secret",
                redirect_uri="http://localhost:5567/callback",
                source_ip="198.51.100.10",
            )

    def test_exchange_code_for_token_returns_id_token_and_nonce(self, monkeypatch):
        """openid 授权码换 token 时应返回带 oidc_issuer 和 nonce 的 id_token"""
        jwt_manager = FakeJWTManager()
        service = OAuth2ProviderService(jwt_manager=jwt_manager, user_getter=lambda _: None)
        oidc_issuer = "https://sso.example.com/api/v1/oauth2"
        restore = _override_oidc_issuer(oidc_issuer)

        app_obj = SimpleNamespace(
            id=100,
            name="Data Formulator",
            client_type="confidential",
            validate_is_active=Mock(),
            is_public_client=lambda: False,
        )
        service.app_service.get_application_by_client_id = Mock(return_value=app_obj)
        service.app_service.validate_client_credentials = Mock(return_value=app_obj)

        auth_code = Mock(
            application_id=100,
            user_id=7,
            redirect_uri="http://localhost:5567/callback",
            scope="openid profile email",
            nonce="nonce-123",
            code_challenge=None,
            code_challenge_method=None,
        )
        auth_code.validate_usable = Mock()
        auth_code.mark_used = Mock()

        user = SimpleNamespace(
            id=7,
            username="zhanghaibin",
            email="zhang@example.com",
            roles=[SimpleNamespace(code="admin")],
        )

        monkeypatch.setattr(AuthorizationCode, "query", QueryStub(auth_code), raising=False)
        monkeypatch.setattr(User, "query", QueryStub(user), raising=False)
        _stub_employee(
            monkeypatch,
            SimpleNamespace(
                id=1,
                code="E001",
                enterprise_wechat_user_id="WeiXinZhang001",
            ),
        )

        try:
            result = service.exchange_code_for_token(
                code="test-code",
                client_id="client-id",
                client_secret="client-secret",
                redirect_uri="http://localhost:5567/callback",
            )

            assert result["id_token"]
            claims = jwt.decode(
                result["id_token"],
                jwt_manager.secret_key,
                algorithms=[jwt_manager.algorithm],
                audience="client-id",
                issuer=oidc_issuer,
            )
            headers = jwt.get_unverified_header(result["id_token"])
            assert claims["sub"] == "7"
            assert claims["nonce"] == "nonce-123"
            assert claims["email"] == "zhang@example.com"
            assert claims["preferred_username"] == "zhanghaibin"
            assert headers["kid"] == settings.jwt_key_id
        finally:
            restore()

    def test_refresh_access_token_returns_new_id_token_without_nonce(self, monkeypatch):
        """refresh_token 刷新时应返回带 oidc_issuer 的新 id_token，且不复用 nonce"""
        jwt_manager = FakeJWTManager()
        oidc_issuer = "https://sso.example.com/api/v1/oauth2"
        restore = _override_oidc_issuer(oidc_issuer)
        refreshed_user = SimpleNamespace(
            id=7,
            username="zhanghaibin",
            email="zhang@example.com",
            is_active=True,
            roles=[SimpleNamespace(code="admin")],
        )
        service = OAuth2ProviderService(
            jwt_manager=jwt_manager,
            user_getter=lambda user_id: refreshed_user if user_id == 7 else None,
        )
        service.app_service.validate_client_credentials = Mock()

        refresh_token = jwt.encode(
            {
                "sub": "7",
                "user_id": 7,
                "token_type": "refresh",
                "exp": datetime.now(timezone.utc) + timedelta(days=1),
                "iat": datetime.now(timezone.utc),
            },
            jwt_manager.secret_key,
            algorithm=jwt_manager.algorithm,
        )

        try:
            result = service.refresh_access_token(
                refresh_token=refresh_token,
                client_id="client-id",
                client_secret="client-secret",
            )

            assert result["access_token"] == "access-token"
            assert result["refresh_token"] == "refresh-token"
            assert result["id_token"]
            assert jwt_manager.access_payload.sub == "7"
            assert jwt_manager.access_payload.extra["iss"] == oidc_issuer
            assert jwt_manager.access_payload.extra["aud"] == "client-id"
            assert jwt_manager.refresh_payload.sub == "7"
            claims = jwt.decode(
                result["id_token"],
                jwt_manager.secret_key,
                algorithms=[jwt_manager.algorithm],
                audience="client-id",
                issuer=oidc_issuer,
            )
            headers = jwt.get_unverified_header(result["id_token"])
            assert claims["sub"] == "7"
            assert "nonce" not in claims
            assert headers["kid"] == settings.jwt_key_id
        finally:
            restore()

    def test_get_userinfo_accepts_access_token_with_audience_claim(self, monkeypatch):
        """userinfo 应能消费带 oidc_issuer 和 aud 的 OAuth access token"""
        jwt_manager = JWTManager(**build_runtime_jwt_settings())
        service = OAuth2ProviderService(jwt_manager=jwt_manager, user_getter=lambda _: None)
        oidc_issuer = "https://sso.example.com/api/v1/oauth2"
        restore = _override_oidc_issuer(oidc_issuer)
        app_obj = SimpleNamespace(
            id=100,
            name="Data Formulator",
            validate_is_active=Mock(),
            validate_source_ip=Mock(),
        )
        service.app_service.get_application_by_client_id = Mock(return_value=app_obj)

        user = SimpleNamespace(
            id=7,
            username="zhanghaibin",
            email="zhang@example.com",
            phone="13800138000",
            is_active=True,
            roles=[SimpleNamespace(code="admin")],
        )

        monkeypatch.setattr(User, "query", QueryStub(user), raising=False)

        from app.domain.sso_role.entities import UserSSORole
        monkeypatch.setattr(
            UserSSORole,
            "get_user_sso_role_codes",
            staticmethod(lambda user_id: ["s001"] if user_id == 7 else []),
        )
        _stub_employee(
            monkeypatch,
            SimpleNamespace(
                id=1,
                code="E001",
                enterprise_wechat_user_id="WeiXinZhang001",
            ),
        )

        access_token = jwt_manager.create_access_token(
            {
                "sub": "7",
                "user_id": 7,
                "username": "WeiXinZhang001",
                "email": "zhang@example.com",
                "roles": ["admin"],
                "iss": oidc_issuer,
                "aud": "client-id",
            }
        )

        try:
            userinfo = service.get_userinfo(access_token)

            assert userinfo["sub"] == "7"
            assert userinfo["preferred_username"] == "zhanghaibin"
            assert userinfo["email"] == "zhang@example.com"
            assert userinfo["roles"] == ["admin"]
            assert userinfo["sso_roles"] == ["s001"]
            assert userinfo["user_code"] == "E001"
            assert userinfo["enterprise_wechat_user_id"] == "WeiXinZhang001"
            assert userinfo["emp_status"] is None
            assert userinfo["primary_external_dept_id"] is None
            assert userinfo["external_dept_ids"] == []
            assert userinfo["post_name"] is None
        finally:
            restore()

    def test_get_userinfo_uses_user_username_as_preferred_username(self, monkeypatch):
        """preferred_username 直接使用 User.username，不依赖员工企微字段"""
        jwt_manager = JWTManager(**build_runtime_jwt_settings())
        service = OAuth2ProviderService(jwt_manager=jwt_manager, user_getter=lambda _: None)
        oidc_issuer = "https://sso.example.com/api/v1/oauth2"
        restore = _override_oidc_issuer(oidc_issuer)
        app_obj = SimpleNamespace(
            id=100,
            name="Data Formulator",
            validate_is_active=Mock(),
            validate_source_ip=Mock(),
        )
        service.app_service.get_application_by_client_id = Mock(return_value=app_obj)

        user = SimpleNamespace(
            id=7,
            username="zhanghaibin",
            email="zhang@example.com",
            phone="13800138000",
            is_active=True,
            roles=[SimpleNamespace(code="admin")],
        )

        monkeypatch.setattr(User, "query", QueryStub(user), raising=False)

        from app.domain.sso_role.entities import UserSSORole
        monkeypatch.setattr(
            UserSSORole,
            "get_user_sso_role_codes",
            staticmethod(lambda user_id: []),
        )
        _stub_employee(
            monkeypatch,
            SimpleNamespace(id=1, code="E001", enterprise_wechat_user_id=None),
        )

        access_token = jwt_manager.create_access_token(
            {
                "sub": "7",
                "user_id": 7,
                "username": None,
                "iss": oidc_issuer,
                "aud": "client-id",
            }
        )

        try:
            userinfo = service.get_userinfo(access_token)
            assert userinfo["preferred_username"] == "zhanghaibin"
            assert userinfo["user_code"] == "E001"
            assert userinfo["enterprise_wechat_user_id"] is None
            assert userinfo["emp_status"] is None
            assert userinfo["external_dept_ids"] == []
        finally:
            restore()

    def _prepare_userinfo_request(
        self,
        monkeypatch,
        *,
        employee,
        org_rels=None,
        dept_rels=None,
        departments=None,
    ):
        """构造可调用 get_userinfo 的服务与 access_token"""
        jwt_manager = JWTManager(**build_runtime_jwt_settings())
        service = OAuth2ProviderService(jwt_manager=jwt_manager, user_getter=lambda _: None)
        oidc_issuer = "https://sso.example.com/api/v1/oauth2"
        restore = _override_oidc_issuer(oidc_issuer)
        app_obj = SimpleNamespace(
            id=100,
            name="Data Formulator",
            validate_is_active=Mock(),
            validate_source_ip=Mock(),
        )
        service.app_service.get_application_by_client_id = Mock(return_value=app_obj)

        user = SimpleNamespace(
            id=7,
            username="zhanghaibin",
            email="zhang@example.com",
            phone="13800138000",
            is_active=True,
            roles=[SimpleNamespace(code="admin")],
        )
        monkeypatch.setattr(User, "query", QueryStub(user), raising=False)

        from app.domain.sso_role.entities import UserSSORole
        monkeypatch.setattr(
            UserSSORole,
            "get_user_sso_role_codes",
            staticmethod(lambda user_id: []),
        )
        _stub_employee(
            monkeypatch,
            employee,
            org_rels=org_rels,
            dept_rels=dept_rels,
            departments=departments,
        )

        access_token = jwt_manager.create_access_token(
            {
                "sub": "7",
                "user_id": 7,
                "username": "WeiXinZhang001",
                "iss": oidc_issuer,
                "aud": "client-id",
            }
        )
        return service, access_token, restore

    def test_get_userinfo_includes_org_profile_from_employee_relations(self, monkeypatch):
        """userinfo 应下发企微 userid、雇佣状态、主部门与全部任职部门 id"""
        employee = SimpleNamespace(
            id=21,
            code="E001",
            enterprise_wechat_user_id="EmployeeTableId",
            primary_org_id=10,
            primary_dept_id=2,
        )
        org_rel = SimpleNamespace(
            employee_id=21,
            org_id=10,
            external_user_id="WeiXinZhang001",
            status=3,
            position="数据仓库工程师",
        )
        departments = [
            SimpleNamespace(id=2, org_id=10, external_dept_id="12"),
            SimpleNamespace(id=3, org_id=10, external_dept_id="34"),
            SimpleNamespace(id=4, org_id=10, external_dept_id=None),
        ]
        dept_rels = [
            SimpleNamespace(employee_id=21, dept_id=2, external_dept_id="12"),
            SimpleNamespace(employee_id=21, dept_id=3, external_dept_id="34"),
            SimpleNamespace(employee_id=21, dept_id=4, external_dept_id=None),
        ]
        service, access_token, restore = self._prepare_userinfo_request(
            monkeypatch,
            employee=employee,
            org_rels=[org_rel],
            dept_rels=dept_rels,
            departments=departments,
        )

        try:
            userinfo = service.get_userinfo(access_token)
            assert userinfo["enterprise_wechat_user_id"] == "WeiXinZhang001"
            assert userinfo["preferred_username"] == "zhanghaibin"
            assert userinfo["emp_status"] == 3
            assert userinfo["primary_external_dept_id"] == "12"
            assert userinfo["external_dept_ids"] == ["12", "34"]
            assert userinfo["post_name"] == "数据仓库工程师"
        finally:
            restore()

    def test_get_userinfo_keeps_zero_emp_status_and_null_fields_without_employee(self, monkeypatch):
        """停职状态 0 应原样返回；无员工时组织字段仍在且为空"""
        employee = SimpleNamespace(
            id=21,
            code="E002",
            enterprise_wechat_user_id=None,
            primary_org_id=10,
            primary_dept_id=None,
        )
        org_rel = SimpleNamespace(
            employee_id=21,
            org_id=10,
            external_user_id="WeiXinLi002",
            status=0,
            position="  ",
        )
        service, access_token, restore = self._prepare_userinfo_request(
            monkeypatch,
            employee=employee,
            org_rels=[org_rel],
        )

        try:
            userinfo = service.get_userinfo(access_token)
            assert userinfo["enterprise_wechat_user_id"] == "WeiXinLi002"
            assert userinfo["emp_status"] == 0
            assert userinfo["post_name"] is None
            assert userinfo["primary_external_dept_id"] is None
            assert userinfo["external_dept_ids"] == []
        finally:
            restore()

        service, access_token, restore = self._prepare_userinfo_request(
            monkeypatch,
            employee=None,
        )
        try:
            userinfo = service.get_userinfo(access_token)
            assert "user_code" not in userinfo
            assert userinfo["preferred_username"] == "zhanghaibin"
            assert userinfo["enterprise_wechat_user_id"] is None
            assert userinfo["emp_status"] is None
            assert userinfo["primary_external_dept_id"] is None
            assert userinfo["external_dept_ids"] == []
            assert userinfo["post_name"] is None
        finally:
            restore()

    def test_get_userinfo_rejects_ip_outside_whitelist(self, monkeypatch):
        """userinfo 应校验带 oidc_issuer 的 access token 对应应用的 IP 白名单"""
        jwt_manager = JWTManager(**build_runtime_jwt_settings())
        service = OAuth2ProviderService(jwt_manager=jwt_manager, user_getter=lambda _: None)
        oidc_issuer = "https://sso.example.com/api/v1/oauth2"
        restore = _override_oidc_issuer(oidc_issuer)

        app_obj = SimpleNamespace(
            id=100,
            name="Data Formulator",
            validate_is_active=Mock(),
            validate_source_ip=Mock(side_effect=ValueError("来源IP不在应用白名单内")),
        )
        service.app_service.get_application_by_client_id = Mock(return_value=app_obj)

        access_token = jwt_manager.create_access_token(
            {
                "sub": "7",
                "user_id": 7,
                "username": "zhanghaibin",
                "iss": oidc_issuer,
                "aud": "client-id",
            }
        )

        try:
            with pytest.raises(ValueError, match="白名单"):
                service.get_userinfo(access_token, source_ip="198.51.100.10")
        finally:
            restore()

    def test_authorization_code_create_code_persists_nonce(self):
        """创建授权码时应保存 nonce"""
        auth_code = AuthorizationCode.create_code(
            application_id=1,
            user_id=2,
            redirect_uri="http://localhost:5567/callback",
            scope="openid profile",
            state="state-1",
            nonce="nonce-123",
            code_challenge="challenge",
            code_challenge_method="S256",
        )

        assert auth_code.nonce == "nonce-123"
