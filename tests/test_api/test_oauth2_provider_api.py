"""OAuth2 Provider API 测试"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import settings
from app.api.v1.oauth2 import create_oauth2_provider_router


@pytest.fixture
def oauth2_service_stub():
    """创建 OAuth2 service 桩对象"""
    service = Mock()
    service.validate_authorize_request.return_value = SimpleNamespace(id=100)
    service.create_authorization_code.return_value = SimpleNamespace(code="code-1")
    service.exchange_code_for_token.return_value = {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "token_type": "bearer",
        "expires_in": 1800,
        "scope": "openid profile",
    }
    service.refresh_access_token.return_value = {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "token_type": "bearer",
        "expires_in": 1800,
        "id_token": "refresh-id-token",
    }
    service.get_userinfo.return_value = {
        "sub": "7",
        "preferred_username": "zhanghaibin",
    }
    return service


@pytest.fixture
def app(oauth2_service_stub):
    """创建测试应用"""
    test_app = FastAPI()
    router = create_oauth2_provider_router(
        oauth2_provider_service=oauth2_service_stub,
        get_current_user=lambda: SimpleNamespace(id=7),
        get_current_user_optional=lambda: None,
        frontend_login_url="/sso/login",
    )
    test_app.include_router(router, prefix="/api/v1")
    return test_app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


class TestOAuth2ProviderAPI:
    """OAuth2 Provider API 行为测试"""

    @pytest.fixture(autouse=True)
    def setup_ip_access(self, monkeypatch):
        """测试中显式关闭代理信任，便于稳定断言 client.host"""
        monkeypatch.setattr(settings, "ip_access", {"trusted_proxies": []}, raising=False)

    def test_authorize_redirect_preserves_nonce(self, client, oauth2_service_stub):
        """未登录授权跳转时应透传 nonce 到前端登录页"""
        response = client.get(
            "/api/v1/oauth2/authorize",
            params={
                "response_type": "code",
                "client_id": "client-id",
                "redirect_uri": "http://localhost:5567/callback",
                "scope": "openid profile",
                "state": "state-1",
                "nonce": "nonce-123",
                "code_challenge": "challenge",
                "code_challenge_method": "S256",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "nonce=nonce-123" in response.headers["location"]

    def test_authorize_confirm_passes_nonce_to_service(self, client, oauth2_service_stub):
        """授权确认时应把 nonce 传给 service"""
        response = client.post(
            "/api/v1/oauth2/authorize",
            json={
                "client_id": "client-id",
                "redirect_uri": "http://localhost:5567/callback",
                "scope": "openid profile",
                "state": "state-1",
                "nonce": "nonce-123",
                "code_challenge": "challenge",
                "code_challenge_method": "S256",
            },
        )

        assert response.status_code == 200
        oauth2_service_stub.create_authorization_code.assert_called_once_with(
            application_id=100,
            user_id=7,
            redirect_uri="http://localhost:5567/callback",
            scope="openid profile",
            state="state-1",
            nonce="nonce-123",
            code_challenge="challenge",
            code_challenge_method="S256",
        )

    def test_token_endpoint_returns_id_token(self, client, oauth2_service_stub):
        """token 端点应把 service 返回的 id_token 直接返回给客户端"""
        oauth2_service_stub.exchange_code_for_token.return_value = {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "id_token": "id-token",
            "token_type": "bearer",
            "expires_in": 1800,
            "scope": "openid profile",
        }

        response = client.post(
            "/api/v1/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "code": "code-1",
                "redirect_uri": "http://localhost:5567/callback",
                "client_id": "client-id",
                "client_secret": "client-secret",
            },
        )

        assert response.status_code == 200
        assert response.json()["id_token"] == "id-token"

    def test_token_endpoint_passes_source_ip_to_service(self, client, oauth2_service_stub):
        """token 端点应把请求来源 IP 透传给 service"""
        response = client.post(
            "/api/v1/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "code": "code-1",
                "redirect_uri": "http://localhost:5567/callback",
                "client_id": "client-id",
                "client_secret": "client-secret",
            },
        )

        assert response.status_code == 200
        oauth2_service_stub.exchange_code_for_token.assert_called_with(
            code="code-1",
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="http://localhost:5567/callback",
            code_verifier=None,
            source_ip="testclient",
        )

    def test_userinfo_endpoint_rejects_ip_outside_whitelist(self, client, oauth2_service_stub):
        """userinfo 端点命中 IP 白名单拒绝时应返回 403"""
        oauth2_service_stub.get_userinfo.side_effect = ValueError("来源IP不在应用白名单内")

        response = client.get(
            "/api/v1/oauth2/userinfo",
            headers={"Authorization": "Bearer access-token"},
        )

        assert response.status_code == 403
        assert response.json()["error"] == "access_denied"
        oauth2_service_stub.get_userinfo.assert_called_once_with(
            "access-token",
            source_ip="testclient",
        )
