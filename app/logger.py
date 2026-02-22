"""
应用日志配置模块

使用 yweb 框架的日志工具，简化日志配置。

推荐用法：
    from yweb.log import get_logger
    
    # 在任何模块顶部直接使用，自动推断模块名
    logger = get_logger()
    # 例如在 app/api/v1/auth.py 中会自动得到 "app.api.v1.auth"
"""

from yweb.log import setup_root_logger

# 导入路径常量
from app.config import CONFIG_PATH, CONFIG_BASE_DIR

# ==================== 日志配置（一行搞定） ====================
# 自动从配置文件加载日志配置，包括 SQL 日志
# 注意：此模块需要在其他模块之前导入，以确保日志配置已初始化
root_logger = setup_root_logger(config_path=CONFIG_PATH, config_base_dir=CONFIG_BASE_DIR)