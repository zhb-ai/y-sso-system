"""OIDC Discovery 端点测试"""

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


class TestOIDCDiscoveryEndpoint:
    """OIDC Discovery 端点测试"""

    def test_openid_configuration_returns_standard_metadata(self):
        """根路径应返回标准 OpenID Connect Discovery JSON"""
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/.well-known/openid-configuration")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

        data = response.json()
        base_url = settings.base_url.rstrip("/")

        assert data["issuer"] == base_url
        assert data["authorization_endpoint"] == f"{base_url}/api/v1/oauth2/authorize"
        assert data["token_endpoint"] == f"{base_url}/api/v1/oauth2/token"
        assert data["userinfo_endpoint"] == f"{base_url}/api/v1/oauth2/userinfo"
        assert data["response_types_supported"] == ["code"]
        assert "authorization_code" in data["grant_types_supported"]
        assert data["subject_types_supported"] == ["public"]

    def test_oauth_authorization_server_metadata_uses_configured_base_url(self):
        """旧元数据端点也应使用配置中的外部 base_url，而不是请求 Host"""
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/api/v1/oauth2/.well-known/oauth-authorization-server")

        assert response.status_code == 200
        data = response.json()
        base_url = settings.base_url.rstrip("/")

        assert data["issuer"] == base_url
        assert data["authorization_endpoint"] == f"{base_url}/api/v1/oauth2/authorize"
        assert data["token_endpoint"] == f"{base_url}/api/v1/oauth2/token"
        assert data["userinfo_endpoint"] == f"{base_url}/api/v1/oauth2/userinfo"
