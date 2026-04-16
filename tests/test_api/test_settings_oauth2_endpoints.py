"""系统设置 OAuth2 对接配置测试"""

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.config import create_config_router
from app.config import settings


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


class TestSettingsOAuth2Endpoints:
    """系统设置中的 OAuth2 对接配置接口测试"""

    def _write_rs256_keys(self, tmp_path: Path):
        """生成临时 RSA 密钥对"""
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        private_path = tmp_path / "jwt_private.pem"
        public_path = tmp_path / "jwt_public.pem"
        private_path.write_text(private_pem, encoding="utf-8")
        public_path.write_text(public_pem, encoding="utf-8")
        return private_path, public_path

    def test_get_oauth2_endpoints_returns_integration_metadata(self, monkeypatch):
        """应返回基于 oidc_issuer 的 OAuth2/OIDC 对接信息"""
        oidc_issuer = "https://sso.example.com/api/v1/oauth2"
        restore = _override_oidc_issuer(oidc_issuer)
        app = FastAPI()
        app.include_router(create_config_router(), prefix="/api/v1")
        client = TestClient(app)
        try:
            response = client.get("/api/v1/settings/oauth2-endpoints")

            assert response.status_code == 200
            payload = response.json()
            data = payload["data"]

            assert data["issuer"] == oidc_issuer
            assert data["discovery_url"] == f"{oidc_issuer}/.well-known/openid-configuration"
            assert data["authorization_endpoint"] == f"{oidc_issuer}/authorize"
            assert data["token_endpoint"] == f"{oidc_issuer}/token"
            assert data["userinfo_endpoint"] == f"{oidc_issuer}/userinfo"
            assert data["pkce_supported"] is True
            assert data["token_signing_algorithm"] == settings.jwt.algorithm
        finally:
            restore()

    def test_get_oauth2_endpoints_reports_jwks_and_pkce_when_enabled(self, tmp_path, monkeypatch):
        """启用 RS256 和 PKCE 后，接口应反映最新能力"""
        private_path, public_path = self._write_rs256_keys(tmp_path)
        oidc_issuer = "https://sso.example.com/api/v1/oauth2"
        restore = _override_oidc_issuer(oidc_issuer)
        monkeypatch.setattr(settings.jwt, "algorithm", "RS256", raising=False)
        monkeypatch.setattr(settings, "jwt_private_key_path", str(private_path), raising=False)
        monkeypatch.setattr(settings, "jwt_public_key_path", str(public_path), raising=False)
        app = FastAPI()
        app.include_router(create_config_router(), prefix="/api/v1")
        client = TestClient(app)
        try:
            response = client.get("/api/v1/settings/oauth2-endpoints")

            assert response.status_code == 200
            data = response.json()["data"]

            assert data["pkce_supported"] is True
            assert data["jwks_uri"] == f"{oidc_issuer}/jwks"
            assert data["token_signing_algorithm"] == "RS256"
        finally:
            restore()

    def test_get_oauth2_endpoints_reports_default_jwks_in_dev(self):
        """默认开发配置应展示已启用的 JWKS URI"""
        app = FastAPI()
        app.include_router(create_config_router(), prefix="/api/v1")
        client = TestClient(app)

        response = client.get("/api/v1/settings/oauth2-endpoints")

        assert response.status_code == 200
        data = response.json()["data"]
        issuer = f"{settings.base_url.rstrip('/')}/api/v1/oauth2"

        assert data["jwks_uri"] == f"{issuer}/jwks"
        assert data["token_signing_algorithm"] == "RS256"
