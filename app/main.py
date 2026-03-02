"""
单点登录系统 API 主模块

职责：应用创建、中间件配置、生命周期管理。
路由注册集中在 app.api.routes 模块。
"""

# 确保日志配置已初始化（必须在其他模块之前）
from app.logger import root_logger  # noqa: F401

from contextlib import asynccontextmanager
from fastapi import FastAPI
import app.database  # 确保数据库初始化（必须在模型导入前）  # noqa: F401
from app.config import settings
from yweb.log import get_logger
from yweb.exceptions import register_exception_handlers
from app.api.cors import DynamicCORSMiddleware
from app.api.middleware import (
    RequestLoggingMiddleware,
    RequestIDMiddleware,
    PerformanceMonitoringMiddleware,
    get_user_info_from_token,
    api_logger,
)
import os

logger = get_logger()


# ==================== 生命周期 ====================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # ---- 启动 ----
    logger.info("单点登录系统API启动完成")
    logger.info(
        f"JWT 配置: Access Token {settings.jwt.access_token_expire_minutes}分钟, "
        f"Refresh Token {settings.jwt.refresh_token_expire_days}天, "
        f"滑动过期 {getattr(settings.jwt, 'refresh_token_sliding_days', 2)}天"
    )

    # 自动扫描路由并同步权限表
    from app.startup import auto_sync_permissions
    auto_sync_permissions(app)

    yield

    # ---- 关闭 ----
    logger.info("单点登录系统API正在关闭")


# ==================== 创建应用 ====================


app = FastAPI(
    title="单点登录系统API",
    description="基于FastAPI的单点登录系统，支持JWT认证、企业微信扫码登录、多应用管理、组织架构同步等功能。",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 注册全局异常处理器
register_exception_handlers(app)


# ==================== 中间件（添加顺序的逆序执行） ====================


# 第 1 个添加 → 最后执行：请求日志
app.add_middleware(
    RequestLoggingMiddleware,
    config=settings.middleware,
    logger=api_logger,
    user_info_getter=get_user_info_from_token,
    enable_sensitive_filter=True,
)

# 第 2 个添加：性能监控
app.add_middleware(PerformanceMonitoringMiddleware)

# 第 3 个添加 → 最先执行：生成请求 ID
app.add_middleware(RequestIDMiddleware)

# IP 访问控制中间件（最先执行，在所有中间件之前拦截非法 IP）
ip_access_config = getattr(settings, 'ip_access', None)
if ip_access_config:
    from yweb.middleware import IPAccessMiddleware
    mw_kwargs = IPAccessMiddleware.from_settings(ip_access_config)
    if mw_kwargs.get("rules"):
        app.add_middleware(IPAccessMiddleware, **mw_kwargs)

# 动态 CORS：从已注册应用的 redirect_uris 自动提取允许的 Origin
from app.domain.application.entities import Application as ApplicationModel
app.add_middleware(
    DynamicCORSMiddleware,
    application_model=ApplicationModel,
    cache_ttl=300,                  # 5 分钟缓存
    allow_localhost=True,           # 开发环境：允许 localhost / 127.0.0.1 任意端口
)


# ==================== 路由注册（一站式） ====================


from app.api.routes import register_all_routes
register_all_routes(app)


# ==================== 静态文件服务 ====================


# 静态文件目录路径
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")




# ==================== 基础端点 ====================


@app.get("/")
def root():
    """根路径"""
    # return {
    #     "message": "欢迎使用单点登录系统API",
    #     "version": "1.0.0",
    #     "docs": "/docs",
    #     "redoc": "/redoc",
    # }

    # 返回前端页面
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/health")
def health_check():
    """健康检查"""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ==================== 前端单页应用路由 ====================

from fastapi.responses import FileResponse

@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    """处理前端单页应用路由和静态文件"""
    # API 路由不应该走到这里（因为已经注册了），但为了安全起见
    if full_path.startswith("api/"):
        return {"status": "error", "message": "Not Found"}
    
    # 构建文件路径
    file_path = os.path.join(static_dir, full_path)
    
    # 如果文件存在，返回文件（处理静态资源如 JS、CSS、图片等）
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # 否则返回 index.html，让前端路由处理（处理前端路由如 /sso/login）
    return FileResponse(os.path.join(static_dir, "index.html"))


# ==================== 调试启动 ====================


if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="单点登录系统API调试启动")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="绑定的主机地址")
    parser.add_argument("--port", type=int, default=8001, help="监听的端口号")
    parser.add_argument("--reload", action="store_true", help="启用自动重载")
    args = parser.parse_args()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )
