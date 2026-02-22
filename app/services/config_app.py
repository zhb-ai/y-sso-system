from typing import Any, Optional
from app.domain.config.entities import SystemConfig, JWTConfig
from app.domain.config.repositories import ConfigRepository


class ConfigApplicationService:
    """配置应用服务"""
    
    def __init__(self, config_repository: ConfigRepository):
        self.config_repository = config_repository
    
    def get_config(self, config_key: str) -> Optional[SystemConfig]:
        """获取配置"""
        return self.config_repository.get_by_key(config_key)
    
    def get_all_configs(self):
        """获取所有配置"""
        return self.config_repository.get_all()
    
    def update_config(self, config_key: str, config_value: Any, description: Optional[str] = None) -> SystemConfig:
        """更新配置"""
        config = self.config_repository.get_by_key(config_key)
        if config:
            config.config_value = config_value
            if description:
                config.description = description
            return self.config_repository.update(config)
        else:
            new_config = SystemConfig(
                config_key=config_key,
                config_value=config_value,
                description=description
            )
            return self.config_repository.create_or_update(new_config)
    
    def get_jwt_config(self) -> JWTConfig:
        """获取JWT配置"""
        # 从数据库获取配置
        config = self.config_repository.get_by_key("jwt")
        
        if config and config.is_active:
            return JWTConfig(**config.config_value)
        else:
            # 数据库中没有配置或配置未激活，使用默认值初始化
            default_config = JWTConfig(
                secret_key="default-secret-key-change-this-in-production",
                algorithm="HS256",
                access_token_expire_minutes=30,
                refresh_token_expire_days=7
            )
            
            # 将默认配置保存到数据库
            self.update_jwt_config(default_config)
            
            return default_config
    
    def update_jwt_config(self, jwt_config: JWTConfig) -> SystemConfig:
        """更新JWT配置"""
        return self.update_config(
            config_key="jwt",
            config_value=jwt_config.__dict__,
            description="JWT配置"
        )
