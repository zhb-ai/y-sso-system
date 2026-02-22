"""
中间件模块

此模块从 yweb 框架导入基础中间件，并提供项目特定的配置。
"""

from fastapi import Request

# 从 yweb 框架导入中间件
from yweb.middleware import (
    RequestLoggingMiddleware,
    RequestIDMiddleware,
    PerformanceMonitoringMiddleware,
    get_request_id,
)

# 从 yweb 框架导入日志过滤钩子
from yweb.log import SensitiveDataFilterHook, log_filter_hook_manager, get_logger

# 项目配置
from app.config import settings

# 创建 API 日志记录器（自动推断为 app.api.middleware）
api_logger = get_logger()


# ==================== 敏感数据过滤配置 ====================
# 注册项目特定的敏感数据过滤器
project_sensitive_filter = SensitiveDataFilterHook(
    sensitive_patterns=[
        # 默认模式（继承）- 匹配包含这些关键词的字段名
        r'.*(password|pwd|passwd).*',           # 密码相关字段
        r'.*(token|access_token|refresh_token).*',  # 认证令牌
        r'.*(secret|key|apikey|api_key).*',     # 密钥和API密钥
        r'.*(credential|credentials).*',       # 凭证信息
        # 项目特定模式 - 保护用户隐私数据
        r'.*(phone|mobile|tel).*',              # 手机号
        r'.*(id_card|idcard).*',                # 身份证号码
        r'.*(email).*',                         # 邮箱地址（可选）
    ],
    sensitive_paths=[
        # 这些API路径的请求/响应数据会被应用敏感数据过滤
        '/auth/login',           # 登录接口（包含密码）
        '/auth/token',           # 获取token接口（包含凭证）
        '/admin/login',          # 管理员登录（包含密码）
        '/user/register',        # 注册接口（包含密码和个人信息）
        '/user/profile',         # 用户资料（包含个人信息）
        '/user/password',        # 修改密码（包含新旧密码）
    ]
)
# 注册到全局钩子，RequestLoggingMiddleware 记录日志时自动对敏感字段脱敏
log_filter_hook_manager.register_hook(project_sensitive_filter)


async def get_user_info_from_token(scope: dict) -> str:
    """从 JWT Token 获取用户信息，用于请求日志记录"""
    try:
        request = Request(scope)
        url = request.url.path
        
        # 跳过登录接口
        if any(url.endswith(path) for path in ['/auth/login', '/auth/token', '/admin/login']):
            return "pre-authentication"
        
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split("Bearer ")[1]
            from app.api.dependencies import auth_service
            token_data = auth_service.verify_token(token)
            if token_data:
                return f"{token_data.username}(id:{token_data.user_id})"
            return f"invalid_token_{token[:8]}..."
        
    except Exception as e:
        api_logger.debug(f"Failed to get user info: {type(e).__name__}: {e}")
    
    return "anonymous"


def create_request_logging_middleware(app):
    """创建请求日志中间件
    
    使用 yweb 的 RequestLoggingMiddleware，传入项目配置。
    
    Args:
        app: FastAPI 应用实例
        
    Returns:
        配置好的 RequestLoggingMiddleware 实例
    """
    return RequestLoggingMiddleware(
        app,
        config=settings.middleware,
        logger=api_logger,
        user_info_getter=get_user_info_from_token,
        enable_sensitive_filter=True  # 启用敏感数据过滤
    )


# 导出所有中间件
__all__ = [
    "RequestLoggingMiddleware",
    "RequestIDMiddleware",
    "PerformanceMonitoringMiddleware",
    "get_request_id",
    "get_user_info_from_token",
    "create_request_logging_middleware",
]
