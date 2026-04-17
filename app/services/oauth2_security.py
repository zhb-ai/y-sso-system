"""OAuth2 / OIDC 安全辅助函数"""

import base64
import hashlib
import inspect
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import serialization
from yweb.auth import JWTManager

from app.config import settings


def get_base_url() -> str:
    """获取系统对外基础地址"""
    return settings.base_url.rstrip("/")


def get_oidc_issuer() -> str:
    """获取 OIDC issuer，默认挂在 /api/v1/oauth2 下"""
    configured_issuer = getattr(settings, "oidc_issuer", None)
    if configured_issuer:
        return str(configured_issuer).rstrip("/")
    return f"{get_base_url()}/api/v1/oauth2"


def build_oidc_url(path: str) -> str:
    """基于 OIDC issuer 构造标准端点 URL"""
    normalized_path = path if path.startswith("/") else f"/{path}"
    return f"{get_oidc_issuer()}{normalized_path}"


def _read_text_file(path: str) -> str:
    """读取文本文件"""
    return Path(path).read_text(encoding="utf-8").strip()


def is_rs256_enabled() -> bool:
    """当前是否启用 RS256"""
    return str(settings.jwt.algorithm).upper() == "RS256"


def get_runtime_jwt_private_key() -> str:
    """获取运行时 JWT 私钥"""
    if getattr(settings, "jwt_private_key_path", None):
        return _read_text_file(settings.jwt_private_key_path)
    return settings.jwt.secret_key


def get_runtime_jwt_public_key() -> Optional[str]:
    """获取运行时 JWT 公钥"""
    public_key_path = getattr(settings, "jwt_public_key_path", None)
    if public_key_path:
        return _read_text_file(public_key_path)

    secret_key = settings.jwt.secret_key
    if "BEGIN PUBLIC KEY" in secret_key:
        return secret_key

    if "PRIVATE KEY" not in secret_key:
        return None

    private_key = serialization.load_pem_private_key(
        secret_key.encode("utf-8"),
        password=None,
    )
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


def build_runtime_jwt_settings() -> dict:
    """构造 setup_auth 使用的 JWT 配置"""
    secret_key = settings.jwt.secret_key
    if is_rs256_enabled():
        secret_key = get_runtime_jwt_private_key()

    runtime_settings = {
        "secret_key": secret_key,
        "algorithm": settings.jwt.algorithm,
        "access_token_expire_minutes": settings.jwt.access_token_expire_minutes,
        "refresh_token_expire_days": settings.jwt.refresh_token_expire_days,
        "refresh_token_sliding_days": getattr(settings.jwt, "refresh_token_sliding_days", 2),
    }
    if "key_id" in inspect.signature(JWTManager.__init__).parameters:
        runtime_settings["key_id"] = get_jwt_key_id()
    return runtime_settings


def get_jwt_key_id() -> str:
    """获取 JWKS key id"""
    return getattr(settings, "jwt_key_id", "sso-rs256-key-1")


def _base64url_uint(value: int) -> str:
    """将整数编码为 base64url"""
    length = max(1, (value.bit_length() + 7) // 8)
    raw = value.to_bytes(length, "big")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def build_jwks() -> dict:
    """构造 JWKS 文档"""
    if not is_rs256_enabled():
        return {"keys": []}

    public_key_pem = get_runtime_jwt_public_key()
    if not public_key_pem:
        return {"keys": []}

    public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
    numbers = public_key.public_numbers()
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": get_jwt_key_id(),
                "use": "sig",
                "alg": "RS256",
                "n": _base64url_uint(numbers.n),
                "e": _base64url_uint(numbers.e),
            }
        ]
    }


def build_pkce_s256_challenge(code_verifier: str) -> str:
    """生成 S256 challenge"""
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
