"""系统配置管理模块

提供系统级键值配置的存储和管理。
使用 Active Record 模式，不引入 Repository 层。
"""

from .entities import SystemConfig

__all__ = ["SystemConfig"]
