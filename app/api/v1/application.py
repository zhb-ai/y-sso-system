"""应用管理 API

提供 SSO 客户端应用的 CRUD、凭证管理、状态管理等功能。
使用动词风格路由，只使用 GET 和 POST 请求。

设计原则（DDD 分层）：
- API 层只负责：参数验证、DTO 转换、异常处理、调用服务层
- 业务逻辑封装在领域模型和服务层
- 捕获 ValueError 统一处理

前端 API 对应：
    GET  /v1/applications/list          → 列表（分页）
    GET  /v1/applications/get           → 详情
    POST /v1/applications/create        → 创建
    POST /v1/applications/update        → 更新
    POST /v1/applications/delete        → 删除
    POST /v1/applications/enable        → 启用
    POST /v1/applications/disable       → 禁用
    POST /v1/applications/reset-secret  → 重置密钥
"""

import json
from typing import Optional, List

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, field_validator

from yweb import DTO
from yweb.response import Resp, PageResponse, ItemResponse, OkResponse
from yweb.log import get_logger

from app.domain.application.services import ApplicationService

logger = get_logger()


# ==================== DTO 定义 ====================


class ApplicationResponse(DTO):
    """应用响应 DTO（不含密钥）"""
    id: int = 0
    name: str = ""
    code: str = ""
    description: Optional[str] = None
    client_id: str = ""
    client_type: str = "confidential"
    redirect_uris: list = []
    logo_url: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator('redirect_uris', mode='before')
    @classmethod
    def parse_redirect_uris(cls, v):
        """将 JSON 字符串解析为列表"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v if isinstance(v, list) else []


class ApplicationWithSecretResponse(ApplicationResponse):
    """包含密钥的应用响应 DTO（仅在创建/重置密钥时返回）"""
    client_secret: str = ""


# ==================== 请求 Schema ====================


class CreateApplicationRequest(BaseModel):
    """创建应用请求"""
    name: str = Field(..., min_length=1, max_length=255, description="应用名称")
    code: str = Field(..., min_length=1, max_length=255, description="应用编码")
    description: Optional[str] = Field(None, description="应用描述")
    client_type: str = Field(
        default="confidential",
        description="客户端类型: confidential（机密/服务端应用）或 public（公开/SPA/移动端）",
    )
    redirect_uris: List[str] = Field(default=[], description="重定向URI列表")
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")


class UpdateApplicationRequest(BaseModel):
    """更新应用请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="应用名称")
    description: Optional[str] = Field(None, description="应用描述")
    client_type: Optional[str] = Field(
        None,
        description="客户端类型: confidential（机密/服务端应用）或 public（公开/SPA/移动端）",
    )
    redirect_uris: Optional[List[str]] = Field(None, description="重定向URI列表")
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")


# ==================== 路由工厂 ====================


def create_application_router() -> APIRouter:
    """创建应用管理路由

    Returns:
        APIRouter 实例
    """

    router = APIRouter(prefix="/applications", tags=["应用管理"])
    app_service = ApplicationService()

    # ==================== 查询接口 ====================

    @router.get(
        "/list",
        response_model=PageResponse[ApplicationResponse],
        summary="获取应用列表",
        description="分页查询 SSO 客户端应用列表，支持按名称/编码搜索、按状态筛选",
    )
    def list_applications(
        keyword: Optional[str] = Query(None, description="搜索关键词（名称/编码）"),
        is_active: Optional[bool] = Query(None, description="是否激活"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    ):
        """获取应用列表"""
        page_result = app_service.list_applications(
            keyword=keyword,
            is_active=is_active,
            page=page,
            page_size=page_size,
        )
        return Resp.OK(ApplicationResponse.from_page(page_result))

    @router.get(
        "/get",
        response_model=ItemResponse[ApplicationResponse],
        summary="获取应用详情",
        description="根据应用ID获取详情",
    )
    def get_application(
        app_id: int = Query(..., description="应用ID"),
    ):
        """获取应用详情"""
        try:
            application = app_service.get_application(app_id)
            return Resp.OK(ApplicationResponse.from_entity(application))
        except ValueError as e:
            return Resp.NotFound(message=str(e))

    # ==================== 写入接口 ====================

    @router.post(
        "/create",
        response_model=ItemResponse[ApplicationWithSecretResponse],
        summary="创建应用",
        description="创建新的 SSO 客户端应用，创建成功后返回 client_id 和 client_secret，密钥仅此次返回",
    )
    def create_application(data: CreateApplicationRequest):
        """创建应用"""
        try:
            application = app_service.create_application(
                name=data.name,
                code=data.code,
                description=data.description,
                client_type=data.client_type,
                redirect_uris=data.redirect_uris,
                logo_url=data.logo_url,
            )
            return Resp.OK(
                ApplicationWithSecretResponse.from_entity(application),
                message="应用创建成功，请妥善保存客户端密钥",
            )
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.post(
        "/update",
        response_model=ItemResponse[ApplicationResponse],
        summary="更新应用",
        description="更新应用信息",
    )
    def update_application(
        data: UpdateApplicationRequest,
        app_id: int = Query(..., description="应用ID"),
    ):
        """更新应用"""
        try:
            update_data = data.model_dump(exclude_unset=True)
            application = app_service.update_application(app_id, **update_data)
            return Resp.OK(ApplicationResponse.from_entity(application), message="更新成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.post(
        "/delete",
        response_model=OkResponse,
        summary="删除应用",
        description="删除应用（软删除）",
    )
    def delete_application(
        app_id: int = Query(..., description="应用ID"),
    ):
        """删除应用"""
        try:
            app_service.delete_application(app_id)
            return Resp.OK(data={"id": app_id}, message="删除成功")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.post(
        "/enable",
        response_model=OkResponse,
        summary="启用应用",
        description="启用指定应用",
    )
    def enable_application(
        app_id: int = Query(..., description="应用ID"),
    ):
        """启用应用"""
        try:
            app_service.enable_application(app_id)
            return Resp.OK(message="应用已启用")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.post(
        "/disable",
        response_model=OkResponse,
        summary="禁用应用",
        description="禁用指定应用",
    )
    def disable_application(
        app_id: int = Query(..., description="应用ID"),
    ):
        """禁用应用"""
        try:
            app_service.disable_application(app_id)
            return Resp.OK(message="应用已禁用")
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    @router.post(
        "/reset-secret",
        response_model=ItemResponse[ApplicationWithSecretResponse],
        summary="重置客户端密钥",
        description="重置客户端密钥，重置后返回新的 client_secret，密钥仅此次返回，旧密钥立即失效",
    )
    def reset_client_secret(
        app_id: int = Query(..., description="应用ID"),
    ):
        """重置客户端密钥"""
        try:
            application, new_secret = app_service.reset_client_secret(app_id)
            app_dict = application.to_dict()
            app_dict['client_secret'] = new_secret
            return Resp.OK(
                ApplicationWithSecretResponse.from_dict(app_dict),
                message="密钥已重置，请妥善保存新的客户端密钥",
            )
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    return router
