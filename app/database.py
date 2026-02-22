"""
数据库初始化模块

使用 yweb 框架的数据库功能，配合项目特定的配置。
"""

# 从 yweb 框架导入数据库管理函数
from yweb.orm import (
    db_manager,
    init_database,
    get_engine,
    get_db,
    on_request_end,
)
from yweb.log import get_logger

# 项目配置
from app.config import settings

# 自动推断日志器名称为 "app.database"
logger = get_logger()

def initialize_database():
    """初始化数据库连接
    
    使用项目配置初始化 yweb 的数据库连接，并激活软删除钩子
    """
    # 使用 yweb 的 init_database 函数（配置对象方式）
    init_database(
        config=settings.database,
        logging_config=settings.logging,
        logger=logger,
    )
    
    logger.info("数据库初始化完成")


# 自动初始化数据库（模块导入时执行）
try:
    initialize_database()
except Exception as e:
    logger.error(f"数据库初始化失败: {e}")
    raise RuntimeError(f"数据库初始化失败: {e}") from e


# 导出所有函数和变量
__all__ = [
    # 管理器单例
    "db_manager",
    # 公开 API
    "initialize_database",
    "get_engine",
    "get_db",
    "on_request_end",
]

