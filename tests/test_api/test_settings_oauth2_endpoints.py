"""系统设置 OAuth2 对接配置测试"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.config import create_config_router
from app.config import settings


class TestSettingsOAuth2Endpoints:
    """系统设置中的 OAuth2 对接配置接口测试"""

    def test_get_oauth2_endpoints_returns_integration_metadata(self):
        """应返回第三方系统对接所需的 OAuth2 端点信息"""
        app = FastAPI()
        app.include_router(create_config_router(), prefix="/api/v1")
        client = TestClient(app)

        response = client.get("/api/v1/settings/oauth2-endpoints")

        assert response.status_code == 200
        payload = response.json()
        data = payload["data"]
        base_url = settings.base_url.rstrip("/")

        assert data["issuer"] == base_url
        assert data["discovery_url"] == f"{base_url}/.well-known/openid-configuration"
        assert data["authorization_endpoint"] == f"{base_url}/api/v1/oauth2/authorize"
        assert data["token_endpoint"] == f"{base_url}/api/v1/oauth2/token"
        assert data["userinfo_endpoint"] == f"{base_url}/api/v1/oauth2/userinfo"
        assert data["pkce_supported"] is False
        assert data["token_signing_algorithm"] == settings.jwt.algorithm
