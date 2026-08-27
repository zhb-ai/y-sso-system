"""下游系统拉取组织员工快照。

部门树沿用 GET /api/v1/org/dept/tree，本模块只组员工行：
企微 userid、登录名、在离职、职位、全部任职部门（含 external_dept_id）。
不包含身份证号。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from yweb.orm import Page


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
