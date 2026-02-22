"""缓存管理 API

为项目接入 yweb.cache 提供的通用缓存管理能力。
"""

from fastapi import APIRouter

from yweb.cache import create_cache_router as create_yweb_cache_router


def create_cache_management_router() -> APIRouter:
    """创建缓存管理路由。

    Returns:
        APIRouter: 缓存管理路由（前缀 /cache）
    """
    router = APIRouter(prefix="/cache", tags=["缓存管理"])
    router.include_router(create_yweb_cache_router())
    return router

