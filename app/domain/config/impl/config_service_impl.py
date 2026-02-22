from typing import Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.domain.config.entities import SystemConfig
from app.domain.config.repositories import ConfigRepository

  
class ConfigServiceImpl(ConfigRepository):
    """配置服务实现"""
    
    def __init__(self, db: Session = None):
        if db:
            self.db = db
        else:
            self.db = next(get_db())
    
    def _model_to_entity(self, model: SystemConfigModel) -> SystemConfig:
        """将数据库模型转换为实体"""
        return SystemConfig(
            id=model.id,
            config_key=model.config_key,
            config_value=model.config_value,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_active=model.is_active
        )
    
    def get_by_key(self, config_key: str) -> Optional[SystemConfig]:
        """通过配置键获取配置"""
        model = self.db.query(SystemConfigModel).filter(
            SystemConfigModel.config_key == config_key
        ).first()
        if model:
            return self._model_to_entity(model)
        return None
    
    def get_all(self) -> List[SystemConfig]:
        """获取所有配置"""
        models = self.db.query(SystemConfigModel).all()
        return [self._model_to_entity(model) for model in models]
    
    def create_or_update(self, config: SystemConfig) -> SystemConfig:
        """创建或更新配置"""
        try:
            # 先查找是否存在
            existing = self.db.query(SystemConfigModel).filter(
                SystemConfigModel.config_key == config.config_key
            ).first()
            
            if existing:
                # 更新现有配置
                existing.config_value = config.config_value
                existing.description = config.description
                existing.is_active = config.is_active
                self.db.commit()
                self.db.refresh(existing)
                return self._model_to_entity(existing)
            else:
                # 创建新配置
                new_config = SystemConfigModel(
                    config_key=config.config_key,
                    config_value=config.config_value,
                    description=config.description,
                    is_active=config.is_active
                )
                self.db.add(new_config)
                self.db.commit()
                self.db.refresh(new_config)
                return self._model_to_entity(new_config)
        except IntegrityError:
            self.db.rollback()
            raise
    
    def update(self, config: SystemConfig) -> SystemConfig:
        """更新配置"""
        if not config.id:
            raise ValueError("Config ID is required for update")
        
        existing = self.db.query(SystemConfigModel).filter(
            SystemConfigModel.id == config.id
        ).first()
        
        if not existing:
            raise ValueError(f"Config with ID {config.id} not found")
        
        existing.config_value = config.config_value
        existing.description = config.description
        existing.is_active = config.is_active
        
        self.db.commit()
        self.db.refresh(existing)
        return self._model_to_entity(existing)
    
    def delete(self, config_key: str) -> None:
        """删除配置"""
        config = self.db.query(SystemConfigModel).filter(
            SystemConfigModel.config_key == config_key
        ).first()
        if config:
            self.db.delete(config)
            self.db.commit()
    
    def get_active_configs(self) -> List[SystemConfig]:
        """获取激活的配置"""
        models = self.db.query(SystemConfigModel).filter(
            SystemConfigModel.is_active == True
        ).all()
        return [self._model_to_entity(model) for model in models]
