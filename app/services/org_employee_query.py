"""组织架构页员工列表查询

yweb 员工列表默认按 id 正序。组织架构页需要最新员工在前，
因此按 id 倒序分页。
"""

from typing import Optional

from yweb.orm import Page


def list_org_employees(
    org_models,
    *,
    org_id: int,
    dept_id: Optional[int] = None,
    emp_status: Optional[int] = None,
    account_status: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
):
    """按组织（可选部门）查询员工，id 倒序分页。"""
    employee_model = org_models.Employee
    emp_org_rel_model = org_models.EmployeeOrgRel
    emp_dept_rel_model = org_models.EmployeeDeptRel
    dept_model = org_models.Department

    emp_ids = {
        rel.employee_id
        for rel in emp_org_rel_model.query.filter_by(org_id=org_id).all()
    }

    if dept_id is not None:
        dept = dept_model.get(dept_id)
        if not dept or dept.org_id != org_id:
            raise ValueError("部门不存在或不属于当前组织")
        dept_emp_ids = {
            rel.employee_id
            for rel in emp_dept_rel_model.query.filter_by(dept_id=dept_id).all()
        }
        emp_ids &= dept_emp_ids

    if emp_status is not None:
        status_emp_ids = {
            rel.employee_id
            for rel in emp_org_rel_model.query.filter(
                emp_org_rel_model.org_id == org_id,
                emp_org_rel_model.status == emp_status,
            ).all()
        }
        emp_ids &= status_emp_ids

    if account_status is not None and hasattr(employee_model, "user_id"):
        emp_ids = _filter_account_status(employee_model, emp_ids, account_status)

    if not emp_ids:
        return Page(
            rows=[],
            total_records=0,
            page=page,
            page_size=page_size,
            total_pages=0,
        )

    return (
        employee_model.query.filter(employee_model.id.in_(emp_ids))
        .order_by(employee_model.id.desc())
        .paginate(page=page, page_size=page_size)
    )


def _filter_account_status(employee_model, emp_ids: set, account_status: int) -> set:
    if account_status == 0:
        no_account = employee_model.query.filter(
            employee_model.id.in_(emp_ids),
            employee_model.user_id.is_(None),
        ).all()
        return {emp.id for emp in no_account}

    if account_status not in (1, -1):
        return emp_ids

    user_rel = getattr(employee_model, "user", None)
    if user_rel is None or not hasattr(user_rel, "property"):
        return emp_ids

    user_model_cls = user_rel.property.mapper.class_
    matching_user_ids = {
        user.id
        for user in user_model_cls.query.filter(
            user_model_cls.is_active == (account_status == 1)
        ).all()
    }
    has_account = employee_model.query.filter(
        employee_model.id.in_(emp_ids),
        employee_model.user_id.in_(matching_user_ids),
    ).all()
    return {emp.id for emp in has_account}
