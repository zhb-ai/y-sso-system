"""系统配置实体

使用 Active Record 模式的 ORM 模型，存储系统级键值配置。
配置值以 JSON 格式存储，支持任意结构的配置数据。

缓存策略：
- 使用 @cached + cache_invalidator 自动失效（符合 YWeb 缓存规范）
- SystemConfig 记录被 update/delete 时，缓存自动失效
- 不存在的 key 返回空字典 {}（避免 None 不缓存导致穿透）

使用示例::

    # 获取配置
    config = SystemConfig.get_by_key("site_info")

    # 设置配置（不存在则创建，存在则更新）
    SystemConfig.set_value("site_info", {"name": "SSO", "desc": "..."})

    # 获取值（带缓存）
    site = SystemConfig.get_value("site_info", default={})
"""

import json
from typing import Any, Optional

from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from yweb.orm import BaseModel
from yweb.cache import cached, cache_invalidator

# 缓存未命中的哨兵值（区分"配置不存在"和"配置值为 None"）
_CACHE_MISS = "__CACHE_MISS__"


@cached(ttl=300, key_prefix="sys_config")
def _cached_get_value(key: str):
    """带缓存的配置读取（300 秒 TTL）

    独立函数是因为 @cached 不能直接装饰 @classmethod。
    返回哨兵值而非 None，确保"配置不存在"也能被缓存，避免缓存穿透。
    """
    config = SystemConfig.get_by_key(key)
    if not config or not config.is_active:
        return _CACHE_MISS
    if not config.config_value:
        return _CACHE_MISS
    try:
        return json.loads(config.config_value)
    except (json.JSONDecodeError, TypeError):
        return config.config_value


class SystemConfig(BaseModel):
    """系统配置模型

    键值对存储，config_value 为 JSON 字符串。
    """
    __tablename__ = "system_config"

    config_key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="配置键（唯一）"
    )

    config_value: Mapped[str] = mapped_column(
        Text, nullable=True, comment="配置值（JSON 格式）"
    )

    description: Mapped[str] = mapped_column(
        String(500), nullable=True, comment="配置说明"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, server_default="1",
        comment="是否启用"
    )

    # ==================== 查询方法 ====================

    @classmethod
    def get_by_key(cls, key: str) -> Optional["SystemConfig"]:
        """通过配置键获取配置"""
        return cls.query.filter(cls.config_key == key).first()

    @classmethod
    def get_value(cls, key: str, default: Any = None) -> Any:
        """获取配置值（带 300 秒内存缓存，自动 JSON 反序列化）

        Args:
            key: 配置键
            default: 默认值（配置不存在或未启用时返回）

        Returns:
            配置值（dict / list / str / int 等）
        """
        result = _cached_get_value(key)
        return default if result is _CACHE_MISS else result

    @classmethod
    def set_value(cls, key: str, value: Any, description: str = None) -> "SystemConfig":
        """设置配置值（不存在则创建，存在则更新）

        缓存失效由 cache_invalidator 自动处理（监听 ORM 事件）。

        Args:
            key: 配置键
            value: 配置值（自动 JSON 序列化）
            description: 配置说明（可选）

        Returns:
            SystemConfig 实例
        """
        json_value = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value

        config = cls.get_by_key(key)
        if config:
            config.config_value = json_value
            if description is not None:
                config.description = description
            config.save(commit=True)
        else:
            config = cls(
                config_key=key,
                config_value=json_value,
                description=description or "",
                is_active=True,
            )
            config.save(commit=True)

        return config


# ==================== 自动缓存失效注册 ====================
# SystemConfig 记录被 update/delete/insert 时，自动清除对应 config_key 的缓存
# 使用 config_key 作为缓存键（而非默认的 id）
cache_invalidator.register(
    SystemConfig,
    _cached_get_value,
    key_extractor=lambda config: config.config_key,
    events=("after_update", "after_delete", "after_insert"),
)
