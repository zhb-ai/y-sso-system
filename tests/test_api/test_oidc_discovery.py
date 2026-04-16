"""OIDC Discovery 端点测试"""

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


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


class TestOIDCDiscoveryEndpoint:
    """OIDC Discovery 端点测试"""

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

    def test_root_openid_configuration_endpoint_is_removed(self):
        """根路径 Discovery 端点应不再对外暴露"""
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/.well-known/openid-configuration")

        assert response.status_code == 404

    def test_api_v1_oauth2_openid_configuration_returns_metadata_for_configured_issuer(self):
        """OAuth2 前缀下的 Discovery 应返回基于 oidc_issuer 的标准元数据"""
        oidc_issuer = "https://sso.example.com/api/v1/oauth2"
        restore = _override_oidc_issuer(oidc_issuer)
        client = TestClient(app, raise_server_exceptions=False)
        try:
            response = client.get("/api/v1/oauth2/.well-known/openid-configuration")

            assert response.status_code == 200
            assert response.headers["content-type"].startswith("application/json")

            data = response.json()

            assert data["issuer"] == oidc_issuer
            assert data["authorization_endpoint"] == f"{oidc_issuer}/authorize"
            assert data["token_endpoint"] == f"{oidc_issuer}/token"
            assert data["userinfo_endpoint"] == f"{oidc_issuer}/userinfo"
            assert data["response_types_supported"] == ["code"]
            assert "authorization_code" in data["grant_types_supported"]
            assert data["subject_types_supported"] == ["public"]
        finally:
            restore()

    def test_oauth_authorization_server_metadata_uses_configured_oidc_issuer(self):
        """OAuth 授权服务器元数据也应使用 oidc_issuer"""
        oidc_issuer = "https://sso.example.com/api/v1/oauth2"
        restore = _override_oidc_issuer(oidc_issuer)
        client = TestClient(app, raise_server_exceptions=False)
        try:
            response = client.get("/api/v1/oauth2/.well-known/oauth-authorization-server")

            assert response.status_code == 200
            data = response.json()

            assert data["issuer"] == oidc_issuer
            assert data["authorization_endpoint"] == f"{oidc_issuer}/authorize"
            assert data["token_endpoint"] == f"{oidc_issuer}/token"
            assert data["userinfo_endpoint"] == f"{oidc_issuer}/userinfo"
        finally:
            restore()

    def test_openid_configuration_includes_jwks_when_rs256_enabled(self, tmp_path, monkeypatch):
        """启用 RS256 后，Discovery 应声明 jwks_uri 和签名算法"""
        private_path, public_path = self._write_rs256_keys(tmp_path)
        oidc_issuer = "https://sso.example.com/api/v1/oauth2"
        restore = _override_oidc_issuer(oidc_issuer)
        monkeypatch.setattr(settings.jwt, "algorithm", "RS256", raising=False)
        monkeypatch.setattr(settings, "jwt_private_key_path", str(private_path), raising=False)
        monkeypatch.setattr(settings, "jwt_public_key_path", str(public_path), raising=False)
        monkeypatch.setattr(settings, "jwt_key_id", "test-rs256-key", raising=False)
        client = TestClient(app, raise_server_exceptions=False)
        try:
            response = client.get("/api/v1/oauth2/.well-known/openid-configuration")

            assert response.status_code == 200
            data = response.json()

            assert data["jwks_uri"] == f"{oidc_issuer}/jwks"
            assert data["id_token_signing_alg_values_supported"] == ["RS256"]
        finally:
            restore()

    def test_default_configuration_exposes_jwks_metadata(self):
        """默认开发配置应在前缀 Discovery 中声明 JWKS 端点"""
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/api/v1/oauth2/.well-known/openid-configuration")

        assert response.status_code == 200
        data = response.json()
        issuer = f"{settings.base_url.rstrip('/')}/api/v1/oauth2"

        assert data["jwks_uri"] == f"{issuer}/jwks"
        assert data["id_token_signing_alg_values_supported"] == ["RS256"]

    def test_default_configuration_jwks_endpoint_returns_key(self):
        """默认开发配置应直接暴露 RSA 公钥"""
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/api/v1/oauth2/jwks")

        assert response.status_code == 200
        data = response.json()
        assert len(data["keys"]) == 1
        assert data["keys"][0]["kty"] == "RSA"
        assert data["keys"][0]["alg"] == "RS256"
        assert data["keys"][0]["kid"] == "sso-dev-rs256-key-1"
        assert data["keys"][0]["n"]
        assert data["keys"][0]["e"]

    def test_jwks_endpoint_returns_rsa_public_key(self, tmp_path, monkeypatch):
        """启用 RS256 后应暴露可供下游验签的 JWKS"""
        private_path, public_path = self._write_rs256_keys(tmp_path)
        monkeypatch.setattr(settings.jwt, "algorithm", "RS256", raising=False)
        monkeypatch.setattr(settings, "jwt_private_key_path", str(private_path), raising=False)
        monkeypatch.setattr(settings, "jwt_public_key_path", str(public_path), raising=False)
        monkeypatch.setattr(settings, "jwt_key_id", "test-rs256-key", raising=False)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/oauth2/jwks")

        assert response.status_code == 200
        data = response.json()
        assert len(data["keys"]) == 1
        assert data["keys"][0]["kty"] == "RSA"
        assert data["keys"][0]["alg"] == "RS256"
        assert data["keys"][0]["kid"] == "test-rs256-key"
