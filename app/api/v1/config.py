"""系统设置 API

提供系统级配置的查看和修改接口。

接口列表：
    GET  /settings/jwt             查看 JWT 配置（只读，来自 settings.yaml）
    GET  /settings/site            获取站点基本信息
    POST /settings/site            更新站点基本信息

设计原则：
- JWT 配置只读展示（来自 settings.yaml，修改需编辑文件并重启）
- 站点信息存储在 SystemConfig 键值表中（Active Record）
- Secret 脱敏显示
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from yweb.response import Resp, OkResponse
from yweb.log import get_logger

from app.domain.config.entities import SystemConfig

logger = get_logger()


# ==================== 请求 Schema ====================


class SiteSettingsRequest(BaseModel):
    """站点基本信息更新请求"""
    system_name: Optional[str] = Field(None, min_length=1, max_length=100, description="系统名称")
    system_desc: Optional[str] = Field(None, max_length=500, description="系统描述")
    system_logo: Optional[str] = Field(None, max_length=500, description="系统 Logo URL")


# ==================== 工具函数 ====================


def _mask_secret(value: str) -> str:
    """脱敏显示密钥"""
    if not value or len(value) <= 8:
        return "****"
    return value[:4] + "****" + value[-4:]


# ==================== 路由工厂 ====================


def create_config_router() -> APIRouter:
    """创建系统设置路由

    Returns:
        APIRouter 实例
    """

    router = APIRouter(prefix="/settings", tags=["系统设置"])

    # ==================== JWT 配置 ====================

    @router.get(
        "/jwt",
        response_model=OkResponse,
        summary="查看 JWT 认证配置（只读）",
        description="查看当前运行时的 JWT 配置（来自 settings.yaml，密钥脱敏显示）。"
                    "JWT 配置只能通过修改 settings.yaml 并重启服务来变更。",
    )
    def get_jwt_settings():
        """查看 JWT 认证配置"""
        from app.config import settings

        jwt = settings.jwt
        return Resp.OK(data={
            "secret_key": _mask_secret(jwt.secret_key),
            "algorithm": jwt.algorithm,
            "access_token_expire_minutes": jwt.access_token_expire_minutes,
            "refresh_token_expire_days": jwt.refresh_token_expire_days,
            "refresh_token_sliding_days": getattr(jwt, 'refresh_token_sliding_days', 2),
        })

    # ==================== 站点基本信息 ====================

    @router.get(
        "/site",
        response_model=OkResponse,
        summary="获取站点基本信息",
        description="获取系统名称、描述、Logo 等基本信息",
    )
    def get_site_settings():
        """获取站点基本信息"""
        defaults = {
            "system_name": "单点登录系统",
            "system_desc": "统一身份认证平台",
            "system_logo": "",
        }
        site = SystemConfig.get_value("site_settings", default=defaults)
        for key, default_val in defaults.items():
            if key not in site:
                site[key] = default_val
        return Resp.OK(data=site)

    @router.post(
        "/site",
        response_model=OkResponse,
        summary="更新站点基本信息",
        description="更新系统名称、描述、Logo 等基本信息",
    )
    def update_site_settings(data: SiteSettingsRequest):
        """更新站点基本信息"""
        try:
            current = SystemConfig.get_value("site_settings", default={})
            update_data = data.model_dump(exclude_unset=True)
            current.update(update_data)

            SystemConfig.set_value(
                "site_settings", current,
                description="站点基本信息",
            )

            logger.info(f"站点信息已更新: {list(update_data.keys())}")
            return Resp.OK(data=current, message="站点信息更新成功")
        except Exception as e:
            return Resp.BadRequest(message=f"保存失败: {e}")

    return router
