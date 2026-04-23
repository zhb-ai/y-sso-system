"""OAuth2 安全辅助函数测试"""

from app.config import settings
from app.services import oauth2_security


class JwtManagerWithKeyId:
    """支持 key_id 参数的 JWTManager 桩"""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        key_id: str | None = None,
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
        refresh_token_sliding_days: int = 2,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.key_id = key_id
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.refresh_token_sliding_days = refresh_token_sliding_days


class JwtManagerWithoutKeyId:
    """不支持 key_id 参数的 JWTManager 桩"""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
        refresh_token_sliding_days: int = 2,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.refresh_token_sliding_days = refresh_token_sliding_days


class TestOAuth2Security:
    """OAuth2 安全辅助函数测试"""

    def test_build_runtime_jwt_settings_includes_key_id_when_supported(self, monkeypatch):
        """JWTManager 支持 key_id 时应透传配置中的 kid"""
        monkeypatch.setattr(oauth2_security, "JWTManager", JwtManagerWithKeyId, raising=False)

        runtime_settings = oauth2_security.build_runtime_jwt_settings()

        assert runtime_settings["key_id"] == settings.jwt_key_id

    def test_build_runtime_jwt_settings_omits_key_id_when_not_supported(self, monkeypatch):
        """JWTManager 不支持 key_id 时应跳过该参数，兼容旧版 yweb"""
        monkeypatch.setattr(oauth2_security, "JWTManager", JwtManagerWithoutKeyId, raising=False)

        runtime_settings = oauth2_security.build_runtime_jwt_settings()

        assert "key_id" not in runtime_settings
