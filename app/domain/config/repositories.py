from abc import ABC, abstractmethod
from typing import Optional, List
from .entities import SystemConfig


class ConfigRepository(ABC):
    """配置仓储接口"""
    
    @abstractmethod
    def get_by_key(self, config_key: str) -> Optional[SystemConfig]:
        """通过配置键获取配置"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[SystemConfig]:
        """获取所有配置"""
        pass
    
    @abstractmethod
    def create_or_update(self, config: SystemConfig) -> SystemConfig:
        """创建或更新配置"""
        pass
    
    @abstractmethod
    def update(self, config: SystemConfig) -> SystemConfig:
        """更新配置"""
        pass
    
    @abstractmethod
    def delete(self, config_key: str) -> None:
        """删除配置"""
        pass
    
    @abstractmethod
    def get_active_configs(self) -> List[SystemConfig]:
        """获取激活的配置"""
        pass
