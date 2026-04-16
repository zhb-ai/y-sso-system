"""
应用配置模块

使用 yweb 框架的配置工具，简化配置管理。
"""

import os
from pydantic import Field

# ==================== 路径常量（放在最前面，供其他模块导入） ====================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = "config/settings.yaml"
CONFIG_BASE_DIR = PROJECT_ROOT

from yweb.config import AppSettings, load_yaml_config, ConfigLoader


class Settings(AppSettings):
    """应用全局配置，继承 yweb 基础配置，只添加业务特有项"""
    enable_console_logging: bool = Field(default=False, description="是否启用控制台日志输出")
    base_url: str = Field(default="http://localhost:8000", description="应用基础URL")
    oidc_issuer: str | None = Field(default=None, description="OIDC Issuer URL")
    jwt_private_key_path: str | None = Field(default=None, description="RS256 私钥文件路径")
    jwt_public_key_path: str | None = Field(default=None, description="RS256 公钥文件路径")
    jwt_key_id: str = Field(default="sso-rs256-key-1", description="JWKS Key ID")


def load_settings() -> Settings:
    """加载配置"""
    return load_yaml_config(CONFIG_PATH, Settings, base_dir=CONFIG_BASE_DIR)


def reload_settings() -> Settings:
    """重新加载配置"""
    global settings
    ConfigLoader.clear_cache()
    settings = load_settings()
    return settings


# 全局配置实例
settings = load_settings()
