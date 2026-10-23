"""下游系统拉取组织员工快照，并按企微 userid 确保一名员工可同步。

部门树沿用 GET /api/v1/org/dept/tree，本模块只组员工行：
企微 userid、登录名、在离职、职位、全部任职部门（含 external_dept_id）。
不包含身份证号，也不返回密码。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from yweb.orm import Page

from app.services.employee_app import EmployeeAccountService


@dataclass
class SyncDeptRecord:
    dept_id: int
    dept_name: Optional[str]
    external_dept_id: Optional[str]
    is_primary: bool


@dataclass
class SyncEmployeeRecord:
    employee_id: int
    name: Optional[str]
    username: Optional[str]
    user_id: Optional[int]
    enterprise_wechat_user_id: Optional[str]
    email: Optional[str]
    mobile: Optional[str]
    emp_status: Optional[int]
    account_status: Optional[int]
    is_active: Optional[bool]
    position: Optional[str]
    primary_dept_id: Optional[int]
    primary_external_dept_id: Optional[str]
    departments: list[SyncDeptRecord] = field(default_factory=list)


@dataclass
class EnsuredSyncEmployee:
    """ensure 接口的服务结果。record 与列表中的一行相同。"""

    record: SyncEmployeeRecord
    existed: bool


def list_employees_for_sync(
    org_models,
    *,
    org_id: int,
    emp_status: Optional[int] = None,
    page: int = 1,
    page_size: int = 100,
) -> Page[SyncEmployeeRecord]:
    """按组织分页导出员工同步行。按 employee.id 升序，便于下游增量对照。"""
    organization = org_models.Organization.get(org_id)
    if organization is None:
        raise ValueError(f"组织不存在: id={org_id}")

    emp_org_rel_model = org_models.EmployeeOrgRel
    rel_query = emp_org_rel_model.query.filter_by(org_id=org_id)
    if emp_status is not None:
        rel_query = rel_query.filter(emp_org_rel_model.status == emp_status)
    org_rels = rel_query.all()
    org_rel_by_emp = {rel.employee_id: rel for rel in org_rels}
    emp_ids = list(org_rel_by_emp)

    if not emp_ids:
        return Page(
            rows=[],
            total_records=0,
            page=page,
            page_size=page_size,
            total_pages=0,
        )

    employee_model = org_models.Employee
    page_result = (
        employee_model.query.filter(employee_model.id.in_(emp_ids))
        .order_by(employee_model.id.asc())
        .paginate(page=page, page_size=page_size)
    )
    page_emp_ids = [emp.id for emp in page_result.rows]
    dept_by_emp, dept_by_id = _load_dept_maps(org_models, page_emp_ids)
    user_by_id = _load_users(page_result.rows)

    records = [
        _build_record(
            emp,
            org_rel=org_rel_by_emp.get(emp.id),
            dept_rels=dept_by_emp.get(emp.id, []),
            dept_by_id=dept_by_id,
            user=user_by_id.get(emp.user_id) if emp.user_id else None,
        )
        for emp in page_result.rows
    ]
    return Page(
        rows=records,
        total_records=page_result.total_records,
        page=page_result.page,
        page_size=page_result.page_size,
        total_pages=page_result.total_pages,
    )


def _load_dept_maps(org_models, employee_ids: list[int]):
    emp_dept_rel_model = org_models.EmployeeDeptRel
    department_model = org_models.Department
    if not employee_ids:
        return {}, {}

    dept_rels = emp_dept_rel_model.query.filter(
        emp_dept_rel_model.employee_id.in_(employee_ids)
    ).all()
    dept_by_emp: dict[int, list] = {}
    for rel in dept_rels:
        dept_by_emp.setdefault(rel.employee_id, []).append(rel)

    dept_ids = {rel.dept_id for rel in dept_rels}
    dept_by_id = {}
    if dept_ids:
        dept_by_id = {
            dept.id: dept
            for dept in department_model.query.filter(department_model.id.in_(dept_ids)).all()
        }
    return dept_by_emp, dept_by_id


def _load_users(employees) -> dict:
    from app.domain.auth.model.user import User

    user_ids = [emp.user_id for emp in employees if emp.user_id]
    if not user_ids:
        return {}
    return {user.id: user for user in User.query.filter(User.id.in_(user_ids)).all()}


def _account_status(emp, user) -> Optional[int]:
    if not hasattr(emp, "user_id"):
        return None
    if emp.user_id is None:
        return 0
    if user is not None and getattr(user, "is_active", False):
        return 1
    return -1


def _text(value) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _build_record(emp, *, org_rel, dept_rels, dept_by_id, user) -> SyncEmployeeRecord:
    wecom = _text(getattr(emp, "enterprise_wechat_user_id", None))
    if wecom is None and org_rel is not None:
        wecom = _text(getattr(org_rel, "external_user_id", None))

    username = _text(getattr(user, "username", None)) if user is not None else None
    if username is None:
        username = wecom

    email = _text(getattr(emp, "email", None))
    if email is None and user is not None:
        email = _text(getattr(user, "email", None))

    mobile = _text(getattr(emp, "mobile", None))
    if mobile is None and user is not None:
        mobile = _text(getattr(user, "phone", None))

    stored_primary = getattr(emp, "primary_dept_id", None)
    dept_rows: list[SyncDeptRecord] = []
    for rel in sorted(dept_rels, key=lambda item: item.dept_id):
        dept = dept_by_id.get(rel.dept_id)
        dept_rows.append(
            SyncDeptRecord(
                dept_id=rel.dept_id,
                dept_name=_text(getattr(dept, "name", None)) if dept is not None else None,
                external_dept_id=_text(getattr(dept, "external_dept_id", None))
                if dept is not None
                else _text(getattr(rel, "external_dept_id", None)),
                is_primary=False,
            )
        )

    if stored_primary is None and len(dept_rows) == 1:
        stored_primary = dept_rows[0].dept_id
    for row in dept_rows:
        row.is_primary = stored_primary is not None and row.dept_id == stored_primary

    primary_ext = None
    for row in dept_rows:
        if row.is_primary:
            primary_ext = row.external_dept_id
            break

    return SyncEmployeeRecord(
        employee_id=emp.id,
        name=_text(getattr(emp, "name", None)),
        username=username,
        user_id=emp.user_id,
        enterprise_wechat_user_id=wecom,
        email=email,
        mobile=mobile,
        emp_status=getattr(org_rel, "status", None) if org_rel is not None else None,
        account_status=_account_status(emp, user),
        is_active=bool(user.is_active) if user is not None else None,
        position=_text(getattr(org_rel, "position", None)) if org_rel is not None else None,
        primary_dept_id=stored_primary,
        primary_external_dept_id=primary_ext,
        departments=dept_rows,
    )


def ensure_employee_for_sync(
    org_models,
    *,
    org_id: int,
    enterprise_wechat_user_id: str,
) -> EnsuredSyncEmployee:
    """按企微 userid 返回该组织的一条员工同步行。

    先查该组织关系表的 external_user_id，再查员工表的 enterprise_wechat_user_id。
    已有员工且已关联 User 时，不请求企微，也不修改本地数据。
    已有员工但没有 User 时，只调用 EmployeeAccountService.create_account_for_employee。
    两处都没有时，调用 WechatWorkSyncService.sync_user_by_userid，
    由该方法请求企微通讯录并在本地创建员工和用户。
    响应不包含 create_account_for_employee 返回的明文密码。
    """
    userid = _text(enterprise_wechat_user_id)
    if userid is None:
        raise ValueError("enterprise_wechat_user_id 不能为空")

    organization = org_models.Organization.get(org_id)
    if organization is None:
        raise ValueError(f"组织不存在: id={org_id}")

    employee, org_rel = _find_employee_in_org(org_models, org_id, userid)
    if employee is not None:
        if getattr(employee, "user_id", None) is None:
            EmployeeAccountService(
                employee_model=org_models.Employee,
            ).create_account_for_employee(employee_id=employee.id)
            employee = org_models.Employee.get(employee.id)
            if employee is None:
                raise ValueError(f"创建用户账号后未找到员工: userid={userid}")
        return EnsuredSyncEmployee(
            record=_record_for_employee(org_models, employee, org_rel),
            existed=True,
        )

    # 用户名冲突时先拒绝。sync_user_by_userid 会先写入员工再创建账号，
    # 此处提前使用与 EmployeeAccountService 相同的错误文本，避免留下没有账号的员工。
    _reject_username_taken(userid)
    synced = _sync_wechat_member(org_models, organization, userid)
    created = synced.get("employee")
    employee_id = getattr(created, "id", None)
    employee = org_models.Employee.get(employee_id) if employee_id is not None else None
    if employee is None:
        raise ValueError(f"企微成员同步后未找到员工: userid={userid}")
    org_rel = org_models.EmployeeOrgRel.query.filter_by(
        org_id=org_id,
        employee_id=employee.id,
    ).first()
    return EnsuredSyncEmployee(
        record=_record_for_employee(org_models, employee, org_rel),
        existed=False,
    )


def _find_employee_in_org(org_models, org_id: int, userid: str):
    """在指定组织中查找这个企微 userid。

    关系表 external_user_id 优先。未命中时再查员工表 enterprise_wechat_user_id，
    并且该员工必须已有本组织的关系。员工表已有、但不属于本组织时拒绝创建。
    """
    rel_model = org_models.EmployeeOrgRel
    employee_model = org_models.Employee

    rel = rel_model.query.filter_by(org_id=org_id, external_user_id=userid).first()
    if rel is not None:
        employee = employee_model.get(rel.employee_id)
        if employee is None:
            raise ValueError(f"员工记录丢失: employee_id={rel.employee_id}")
        return employee, rel

    matched = employee_model.query.filter_by(enterprise_wechat_user_id=userid).all()
    for employee in matched:
        rel = rel_model.query.filter_by(
            org_id=org_id,
            employee_id=employee.id,
        ).first()
        if rel is not None:
            return employee, rel
    if matched:
        raise ValueError(
            f"已有员工使用该企微 userid，但该员工不属于组织 id={org_id}: userid={userid}"
        )
    return None, None


def _reject_username_taken(username: str) -> None:
    from app.domain.auth.model.user import User

    if User.get_by_username(username) is not None:
        raise ValueError(f"用户名已存在: {username}")


def _sync_wechat_member(org_models, organization, userid: str):
    from app.domain.wechat_work.client import WechatWorkClient
    from app.domain.wechat_work.sync_service import WechatWorkSyncService

    client = WechatWorkClient.from_organization(organization)
    return WechatWorkSyncService(client, org_models).sync_user_by_userid(
        organization,
        userid,
    )


def _record_for_employee(org_models, employee, org_rel) -> SyncEmployeeRecord:
    dept_by_emp, dept_by_id = _load_dept_maps(org_models, [employee.id])
    user_by_id = _load_users([employee])
    user = user_by_id.get(employee.user_id) if employee.user_id else None
    return _build_record(
        employee,
        org_rel=org_rel,
        dept_rels=dept_by_emp.get(employee.id, []),
        dept_by_id=dept_by_id,
        user=user,
    )
