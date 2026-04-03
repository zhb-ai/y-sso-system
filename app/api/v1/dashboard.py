"""仪表盘 API

提供系统概览统计数据。

前端 API 对应：
    GET /v1/dashboard/statistics → 统计概览
"""

from fastapi import APIRouter

from yweb.response import Resp, ItemResponse
from yweb.orm import DTO


# ==================== DTO 定义 ====================


class DashboardStatistics(DTO):
    """仪表盘统计数据"""
    application_count: int = 0
    user_count: int = 0
    employee_count: int = 0
    department_count: int = 0


# ==================== 路由工厂 ====================


def create_dashboard_router(dashboard_service) -> APIRouter:
    """创建仪表盘路由

    Args:
        dashboard_service: DashboardAppService 实例

    Returns:
        APIRouter 实例
    """
    router = APIRouter(prefix="/dashboard", tags=["仪表盘"])

    @router.get(
        "/statistics",
        response_model=ItemResponse[DashboardStatistics],
        summary="获取仪表盘统计数据",
    )
    def get_statistics():
        """获取系统概览统计：应用数、过去24小时活跃用户数、员工数、部门数

        user_count: 过去24小时内登录过的用户数量（基于 last_login_at）
        """
        stats = dashboard_service.get_statistics()
        return Resp.OK(DashboardStatistics.from_dict(stats))

    return router
