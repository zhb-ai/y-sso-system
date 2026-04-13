"""OAuth2 Provider Service 测试"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.domain.application.entities import AuthorizationCode
from app.domain.application.services import OAuth2ProviderService
from app.domain.auth.model.user import User
from yweb.orm import init_database


class QueryStub:
    """最小查询桩对象"""

    def __init__(self, result):
        self.result = result

    def filter_by(self, **kwargs):
        return self

    def first(self):
        return self.result


class FakeJWTManager:
    """记录 TokenPayload 的最小 JWT 管理器"""

    access_token_expire_minutes = 30

    def __init__(self):
        self.access_payload = None
        self.refresh_payload = None

    def create_access_token(self, payload):
        self.access_payload = payload
        return "access-token"

    def create_refresh_token(self, payload):
        self.refresh_payload = payload
        return "refresh-token"


class TestOAuth2ProviderService:
    """OAuth2 Provider Service 行为测试"""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """初始化事务管理器所需的最小数据库环境"""
        engine, _ = init_database("sqlite:///:memory:")
        yield
        engine.dispose()

    def test_exchange_code_for_token_uses_user_id_as_sub(self, monkeypatch):
        """授权码换 token 时，JWT 的 sub 应统一为用户 ID 字符串"""
        jwt_manager = FakeJWTManager()
        service = OAuth2ProviderService(jwt_manager=jwt_manager, user_getter=lambda _: None)

        service.app_service.validate_client_credentials = Mock(
            return_value=SimpleNamespace(id=100, name="Data Formulator")
        )

        auth_code = Mock(
            application_id=100,
            user_id=7,
            redirect_uri="http://localhost:5567/callback",
            scope="openid profile email",
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
