"""组织架构页员工列表查询测试"""

import pytest

from yweb.orm import BaseModel, init_database

_ORG_MODELS = None


@pytest.fixture
def org_models():
    """每个测试使用独立内存库，组织模型只创建一次，避免重复注册"""
    global _ORG_MODELS
    engine, _ = init_database("sqlite:///:memory:")
    if _ORG_MODELS is None:
        from yweb.organization import create_org_models

        _ORG_MODELS = create_org_models(table_prefix="orgq_")
    BaseModel.metadata.create_all(bind=engine)
    yield _ORG_MODELS
    engine.dispose()


def _seed_org_employees(models, names):
    organization = models.Organization(name="测试组织", code="org-query")
    organization.add(True)
    employees = []
    for name in names:
        employee = models.Employee(name=name)
        employee.add(True)
        models.EmployeeOrgRel(
            employee_id=employee.id,
            org_id=organization.id,
            status=3,
        ).add(True)
        employees.append(employee)
    return organization, employees


class TestOrgEmployeeQuery:
    """组织架构页员工列表应按 id 倒序"""

    def test_list_returns_newest_employee_first(self, org_models):
        """同一组织下，后创建的员工应排在列表前面"""
        from app.services.org_employee_query import list_org_employees

        organization, employees = _seed_org_employees(
            org_models, ["甲", "乙", "丙"]
        )

        page = list_org_employees(
            org_models, org_id=organization.id, page=1, page_size=10
        )

        assert [row.id for row in page.rows] == [
            employees[2].id,
            employees[1].id,
            employees[0].id,
        ]

    def test_list_paginates_from_newest(self, org_models):
        """倒序后第一页应是最新的两条，而不是最早的两条"""
        from app.services.org_employee_query import list_org_employees

        organization, employees = _seed_org_employees(
            org_models, ["甲", "乙", "丙"]
        )

        page = list_org_employees(
            org_models, org_id=organization.id, page=1, page_size=2
        )

        assert [row.id for row in page.rows] == [employees[2].id, employees[1].id]
        assert page.total_records == 3

    def test_list_returns_empty_page_when_org_has_no_employees(self, org_models):
        """组织下没有员工时应返回空列表"""
        from app.services.org_employee_query import list_org_employees

        organization = org_models.Organization(name="空组织", code="empty-org")
        organization.add(True)

        page = list_org_employees(
            org_models, org_id=organization.id, page=1, page_size=10
        )

        assert page.rows == []
        assert page.total_records == 0

    def test_list_rejects_department_from_another_org(self, org_models):
        """部门不属于当前组织时应报错"""
        from app.services.org_employee_query import list_org_employees

        organization, _ = _seed_org_employees(org_models, ["甲"])
        other_org = org_models.Organization(name="其他组织", code="other-org")
        other_org.add(True)
        other_dept = org_models.Department(
            name="其他部门", code="other-dept", org_id=other_org.id
        )
        other_dept.add(True)

        with pytest.raises(ValueError, match="部门"):
            list_org_employees(
                org_models,
                org_id=organization.id,
                dept_id=other_dept.id,
                page=1,
                page_size=10,
            )
