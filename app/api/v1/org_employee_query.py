"""组织架构页员工列表 API（id 倒序）"""

from typing import Optional

from fastapi import APIRouter, Query

from yweb.organization.schemas.employee import EmployeeResponse
from yweb.response import PageResponse, Resp

from app.services.org_employee_query import list_org_employees


def create_org_employee_query_router(org_models) -> APIRouter:
    """创建组织架构页员工倒序列表路由"""
    router = APIRouter()
    emp_org_rel_model = org_models.EmployeeOrgRel

    def _compute_account_status(emp) -> Optional[int]:
        if not hasattr(emp, "user_id"):
            return None
        if getattr(emp, "user_id", None) is None:
            return 0
        user = getattr(emp, "user", None)
        if user and getattr(user, "is_active", False):
            return 1
        return -1

    def _build_row(emp, org_id: int) -> EmployeeResponse:
        data = emp.to_dict()
        account_status = _compute_account_status(emp)
        if account_status is not None:
            data["account_status"] = account_status
        org_rel = emp_org_rel_model.query.filter_by(
            employee_id=emp.id, org_id=org_id
        ).first()
        if org_rel:
            data["emp_no"] = org_rel.emp_no
            data["position"] = org_rel.position
            data["emp_status"] = org_rel.status
            data["status"] = org_rel.status
        return EmployeeResponse.from_dict(data)

    @router.get(
        "/org/employees",
        response_model=PageResponse[EmployeeResponse],
        summary="组织架构页员工列表（倒序）",
        description="按员工 id 倒序分页，最新员工在前。可按组织和部门筛选。",
    )
    def list_employees_desc(
        org_id: int = Query(..., description="组织ID"),
        dept_id: Optional[int] = Query(None, description="按部门筛选"),
        emp_status: Optional[int] = Query(None, description="按雇佣状态筛选"),
        account_status: Optional[int] = Query(None, description="按账号状态筛选"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    ):
        try:
            page_result = list_org_employees(
                org_models,
                org_id=org_id,
                dept_id=dept_id,
                emp_status=emp_status,
                account_status=account_status,
                page=page,
                page_size=page_size,
            )
        except ValueError as exc:
            return Resp.BadRequest(message=str(exc))

        page_result.rows = [_build_row(emp, org_id) for emp in page_result.rows]
        return Resp.OK(data=page_result)

    return router
