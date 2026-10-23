"""下游系统组织同步 API。

职责：给 HMind 等业务系统导出员工快照，并按企微 userid 确保一名员工可同步。
本层只做参数校验、DTO 转换、调用 Service。

部门树沿用已有 GET /api/v1/org/dept/tree，不再另建。

端点：
| GET  | /org/sync/employees        | 分页导出员工同步行（含任职部门与岗位） |
| POST | /org/sync/employees/ensure | 按企微 userid 返回一名员工同步行 |
"""

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from yweb import DTO
from yweb.response import ItemResponse, PageResponse, Resp

from app.services.org_sync import ensure_employee_for_sync, list_employees_for_sync


class SyncEmployeeDeptData(DTO):
    """员工的一条部门任职。"""

    dept_id: int = Field(..., description="SSO 本地部门 id")
    dept_name: Optional[str] = Field(None, description="部门名称")
    external_dept_id: Optional[str] = Field(
        None,
        description="企微/乐享部门 id，对应下游 Department.external_dept_id",
    )
    is_primary: bool = Field(
        False,
        description="是否主部门：已维护 primary_dept_id 时按该值；未维护且仅一个部门时为 true",
    )


class SyncEmployeeData(DTO):
    """一条员工同步行。不含身份证号。"""

    employee_id: int = Field(..., description="SSO 员工 id")
    name: Optional[str] = Field(None, description="员工姓名或通讯录显示名")
    username: Optional[str] = Field(
        None,
        description="登录名；有 User 时取 User.username，否则回退企微 userid",
    )
    user_id: Optional[int] = Field(None, description="关联的 SSO User.id，无账号则为空")
    enterprise_wechat_user_id: Optional[str] = Field(
        None,
        description="企微 userid，与乐享 staff_id、下游 User.username 对齐",
    )
    email: Optional[str] = Field(None, description="邮箱；员工表优先，否则 User.email")
    mobile: Optional[str] = Field(None, description="手机号；员工表优先，否则 User.phone")
    emp_status: Optional[int] = Field(
        None,
        description="雇佣状态：-1 离职，0 停职，1 待入职，2 试用，3 在职",
    )
    account_status: Optional[int] = Field(
        None,
        description="账号状态：1 已激活，-1 已禁用，0 未绑定 User",
    )
    is_active: Optional[bool] = Field(
        None,
        description="关联 User.is_active；无账号时为空",
    )
    position: Optional[str] = Field(None, description="组织任职上的职位/岗位名")
    primary_dept_id: Optional[int] = Field(None, description="主部门的 SSO 部门 id")
    primary_external_dept_id: Optional[str] = Field(
        None,
        description="主部门的企微/乐享部门 id",
    )
    departments: list[SyncEmployeeDeptData] = Field(
        default_factory=list,
        description="全部任职部门，按 dept_id 升序",
    )


class EnsureSyncEmployeeRequest(BaseModel):
    """按企微 userid 确保一名员工，并返回同步行。"""

    org_id: int = Field(..., description="组织 ID，当前生产一般为 1")
    enterprise_wechat_user_id: str = Field(
        ...,
        description="企微 userid。服务会去掉首尾空白，空白则拒绝",
    )


class EnsureSyncEmployeeData(SyncEmployeeData):
    """一名员工的同步行。字段与列表单行相同，并标明调用前是否已有该员工。"""

    existed: bool = Field(
        ...,
        description=(
            "调用前该组织是否已有这名员工。"
            "已有员工、本次只创建用户账号时为 true；"
            "本次从企微通讯录新建员工时为 false"
        ),
    )


def _sync_employee_kwargs(row) -> dict:
    """把服务层同步行转成与列表接口相同的 DTO 字段。"""
    return {
        "employee_id": row.employee_id,
        "name": row.name,
        "username": row.username,
        "user_id": row.user_id,
        "enterprise_wechat_user_id": row.enterprise_wechat_user_id,
        "email": row.email,
        "mobile": row.mobile,
        "emp_status": row.emp_status,
        "account_status": row.account_status,
        "is_active": row.is_active,
        "position": row.position,
        "primary_dept_id": row.primary_dept_id,
        "primary_external_dept_id": row.primary_external_dept_id,
        "departments": [
            SyncEmployeeDeptData(
                dept_id=dept.dept_id,
                dept_name=dept.dept_name,
                external_dept_id=dept.external_dept_id,
                is_primary=dept.is_primary,
            )
            for dept in row.departments
        ],
    }


def create_org_sync_router(org_models) -> APIRouter:
    """创建下游组织同步路由。"""
    router = APIRouter()

    @router.get(
        "/org/sync/employees",
        response_model=PageResponse[SyncEmployeeData],
        summary="下游同步：分页导出员工",
        description=(
            "给下游系统一次拉齐员工、任职部门与岗位。"
            "部门树请用 GET /api/v1/org/dept/tree。"
            "认证：先 POST /api/v1/auth/token（或 /auth/login）用账号密码换 access_token，"
            "再带 Authorization: Bearer <token>；需要 organization:manage 权限。"
        ),
    )
    def list_sync_employees(
        org_id: int = Query(..., description="组织 ID，当前生产一般为 1"),
        emp_status: Optional[int] = Query(
            None,
            description="按雇佣状态筛选；不传则在职与离职都返回",
        ),
        page: int = Query(1, ge=1, description="页码，从 1 起"),
        page_size: int = Query(100, ge=1, le=200, description="每页条数，最大 200"),
    ):
        try:
            page_result = list_employees_for_sync(
                org_models,
                org_id=org_id,
                emp_status=emp_status,
                page=page,
                page_size=page_size,
            )
        except ValueError as exc:
            return Resp.BadRequest(message=str(exc))

        page_result.rows = [
            SyncEmployeeData(**_sync_employee_kwargs(row))
            for row in page_result.rows
        ]
        return Resp.OK(data=page_result)

    @router.post(
        "/org/sync/employees/ensure",
        response_model=ItemResponse[EnsureSyncEmployeeData],
        summary="下游同步：按企微 userid 确保一名员工",
        description=(
            "给下游系统按企微 userid 取回与 GET /org/sync/employees 相同的一行，不放进 rows。"
            "该组织已有员工且已关联 User 时直接返回，不请求企微，也不修改本地数据。"
            "已有员工但没有 User 时，只创建用户账号，响应不返回明文密码。"
            "员工和 User 都不存在时，按 userid 读取企微通讯录并创建员工和用户。"
            "认证与 GET /org/sync/employees 相同：已登录且具备 organization:manage。"
        ),
    )
    def ensure_sync_employee(body: EnsureSyncEmployeeRequest):
        try:
            result = ensure_employee_for_sync(
                org_models,
                org_id=body.org_id,
                enterprise_wechat_user_id=body.enterprise_wechat_user_id,
            )
        except ValueError as exc:
            return Resp.BadRequest(message=str(exc))
        return Resp.OK(
            data=EnsureSyncEmployeeData(
                **_sync_employee_kwargs(result.record),
                existed=result.existed,
            )
        )

    return router
