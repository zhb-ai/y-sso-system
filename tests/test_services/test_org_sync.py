"""下游员工同步查询测试。"""

import pytest

from yweb.orm import BaseModel, init_database

from app.domain.auth.model.user import User
from app.models_registry import ensure_dynamic_models
from app.services.org_sync import list_employees_for_sync


@pytest.fixture
def org_models():
    """每个测试独立内存库；组织模型走项目注册（含企微字段）。"""
    engine, _ = init_database("sqlite:///:memory:")
    registry = ensure_dynamic_models()
    BaseModel.metadata.create_all(bind=engine)
    yield registry.org_models
    engine.dispose()


def _seed_company(models, *, code="sync-org"):
    organization = models.Organization(name="测试组织", code=code, is_active=True)
    organization.add(True)
    return organization


def _add_dept(models, organization, *, name, external_dept_id):
    dept = models.Department(
        name=name,
        org_id=organization.id,
        level=1,
        sort_order=0,
        is_active=True,
        external_dept_id=external_dept_id,
    )
    dept.add(True)
    return dept


def _add_user(*, username, is_active=True, email=None, phone=None, name=None):
    user = User(
        username=username,
        password_hash="hashed",
        is_active=is_active,
        email=email,
        phone=phone,
        name=name or username,
    )
    user.add(True)
    return user


def _add_employee(
    models,
    organization,
    *,
    name,
    wecom,
    status=3,
    position=None,
    user=None,
    depts=None,
    mobile=None,
    email=None,
    primary_dept_id=None,
):
    employee = models.Employee(
        name=name,
        mobile=mobile,
        email=email,
        gender=0,
        is_senior=False,
        user_id=user.id if user is not None else None,
        enterprise_wechat_user_id=wecom,
        primary_dept_id=primary_dept_id,
    )
    employee.add(True)
    models.EmployeeOrgRel(
        employee_id=employee.id,
        org_id=organization.id,
        status=status,
        position=position,
        external_user_id=wecom,
    ).add(True)
    for dept in depts or []:
        models.EmployeeDeptRel(employee_id=employee.id, dept_id=dept.id).add(True)
    return employee


class TestListEmployeesForSync:
    """同步接口应按稳定顺序导出任职与岗位，且不含身份证号。"""

    def test_missing_org_raises(self, org_models):
        """组织不存在时应报错"""
        with pytest.raises(ValueError, match="组织不存在"):
            list_employees_for_sync(org_models, org_id=99999)

    def test_empty_org_returns_empty_page(self, org_models):
        """组织下没有员工时应返回空分页"""
        organization = _seed_company(org_models)
        page = list_employees_for_sync(org_models, org_id=organization.id)
        assert page.rows == []
        assert page.total_records == 0

    def test_row_contains_wecom_position_and_dept(self, org_models):
        """在职员工应带出企微 userid、职位和任职部门的外部 id"""
        organization = _seed_company(org_models)
        dept = _add_dept(org_models, organization, name="开发组", external_dept_id="50")
        user = _add_user(username="anhao", phone="13800001111", name="安浩")
        _add_employee(
            org_models,
            organization,
            name="开发组-安浩-商务助理",
            wecom="anhao",
            position="商务助理",
            user=user,
            depts=[dept],
        )

        page = list_employees_for_sync(org_models, org_id=organization.id)
        assert page.total_records == 1
        row = page.rows[0]
        assert row.enterprise_wechat_user_id == "anhao"
        assert row.username == "anhao"
        assert row.position == "商务助理"
        assert row.emp_status == 3
        assert row.account_status == 1
        assert row.is_active is True
        assert row.mobile == "13800001111"
        assert row.primary_external_dept_id == "50"
        assert len(row.departments) == 1
        assert row.departments[0].external_dept_id == "50"
        assert row.departments[0].is_primary is True
        assert not hasattr(row, "id_card")

    def test_includes_resigned_unless_filtered(self, org_models):
        """默认包含离职员工；按 emp_status=3 筛选时应排除"""
        organization = _seed_company(org_models)
        _add_employee(
            org_models, organization, name="在职", wecom="on_duty", status=3
        )
        _add_employee(
            org_models, organization, name="离职", wecom="left_one", status=-1
        )

        all_rows = list_employees_for_sync(org_models, org_id=organization.id)
        assert {row.enterprise_wechat_user_id for row in all_rows.rows} == {
            "on_duty",
            "left_one",
        }

        active_only = list_employees_for_sync(
            org_models, org_id=organization.id, emp_status=3
        )
        assert [row.enterprise_wechat_user_id for row in active_only.rows] == ["on_duty"]

    def test_multiple_depts_without_primary_mark_none(self, org_models):
        """未维护主部门且任职多于一个时，不臆造主部门"""
        organization = _seed_company(org_models)
        dept_a = _add_dept(org_models, organization, name="开发组", external_dept_id="50")
        dept_b = _add_dept(org_models, organization, name="支持组", external_dept_id="49")
        _add_employee(
            org_models,
            organization,
            name="双部门",
            wecom="dual",
            depts=[dept_a, dept_b],
        )

        row = list_employees_for_sync(org_models, org_id=organization.id).rows[0]
        assert row.primary_dept_id is None
        assert row.primary_external_dept_id is None
        assert {dept.external_dept_id for dept in row.departments} == {"49", "50"}
        assert all(dept.is_primary is False for dept in row.departments)

    def test_paginates_by_employee_id_asc(self, org_models):
        """分页按员工 id 升序，第一页是较早创建的人"""
        organization = _seed_company(org_models)
        first = _add_employee(org_models, organization, name="甲", wecom="a")
        second = _add_employee(org_models, organization, name="乙", wecom="b")
        _add_employee(org_models, organization, name="丙", wecom="c")

        page = list_employees_for_sync(
            org_models, org_id=organization.id, page=1, page_size=2
        )
        assert [row.employee_id for row in page.rows] == [first.id, second.id]
        assert page.total_records == 3
        assert page.has_next is True
