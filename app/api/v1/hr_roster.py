"""花名册查询 API

供已登录且具备组织架构权限的系统，按用户名读取员工花名册快照。

    GET /employees/hr-roster?username=
"""

from typing import Any, Optional, Type

from fastapi import APIRouter, Query

from yweb import DTO
from yweb.response import ItemResponse, Resp

from app.services.hr_roster_app import get_hr_roster_by_username


def create_hr_roster_router(employee_model: Type) -> APIRouter:
    """创建花名册查询路由。"""
    router = APIRouter()

    class HrRosterResponse(DTO):
        """员工花名册快照。"""
        username: str = ""
        employee_id: int = 0
        hr_roster: Optional[dict[str, Any]] = None

    @router.get(
        "/employees/hr-roster",
        response_model=ItemResponse[HrRosterResponse],
        summary="按用户名查询花名册",
        description=(
            "参数 username 是用户管理页的用户名，对应 user.username。"
            "返回该用户关联员工最近一次执行花名册脚本时保存的 JSON。"
            "花名册尚未拉取、用户不存在或未关联员工时返回 404。"
        ),
    )
    def get_employee_hr_roster(
        username: str = Query(..., min_length=1, description="用户名，对应 user.username"),
    ):
        try:
            found = get_hr_roster_by_username(employee_model, username)
        except ValueError as exc:
            return Resp.NotFound(message=str(exc))
        return Resp.OK(HrRosterResponse(
            username=found["username"],
            employee_id=found["employee_id"],
            hr_roster=found["hr_roster"],
        ))

    return router
