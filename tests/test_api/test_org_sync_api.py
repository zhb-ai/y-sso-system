"""下游员工同步 API 测试。"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from yweb.orm import BaseModel, init_database

from app.api.v1.org_sync import create_org_sync_router
from app.domain.auth.model.user import User
from app.models_registry import ensure_dynamic_models


def _setup():
    engine, _ = init_database("sqlite:///:memory:")
    registry = ensure_dynamic_models()
    BaseModel.metadata.create_all(bind=engine)
    return registry.org_models, engine


def _client(org_models):
    app = FastAPI()
    app.include_router(create_org_sync_router(org_models), prefix="/api/v1")
    return TestClient(app)


class TestOrgSyncEmployeesApi:
    """同步导出接口应返回下游可落库的字段，且不带身份证号。"""

    def test_missing_org_returns_bad_request(self):
        """组织不存在时应 400"""
        org_models, engine = _setup()
        try:
            response = _client(org_models).get(
                "/api/v1/org/sync/employees",
                params={"org_id": 99999},
            )
            assert response.status_code == 400
            payload = response.json()
            assert payload["status"] == "error"
            assert "组织不存在" in payload["message"]
        finally:
            engine.dispose()

    def test_list_returns_sync_fields_without_id_card(self):
        """成功响应含企微 userid、岗位、任职部门，不含身份证号"""
        org_models, engine = _setup()
        try:
            organization = org_models.Organization(
                name="洋帆", code="hmind-sync", is_active=True
            )
            organization.add(True)
            dept = org_models.Department(
                name="开发组",
                org_id=organization.id,
                level=1,
                sort_order=0,
                is_active=True,
                external_dept_id="50",
            )
            dept.add(True)
            user = User(
                username="anhao",
                password_hash="hashed",
                is_active=True,
                name="安浩",
            )
            user.add(True)
            employee = org_models.Employee(
                name="开发组-安浩-商务助理",
                gender=0,
                is_senior=False,
                user_id=user.id,
                enterprise_wechat_user_id="anhao",
            )
            employee.add(True)
            org_models.EmployeeOrgRel(
                employee_id=employee.id,
                org_id=organization.id,
                status=3,
                position="商务助理",
                external_user_id="anhao",
            ).add(True)
            org_models.EmployeeDeptRel(
                employee_id=employee.id, dept_id=dept.id
            ).add(True)

            response = _client(org_models).get(
                "/api/v1/org/sync/employees",
                params={"org_id": organization.id, "page": 1, "page_size": 50},
            )
            assert response.status_code == 200
            payload = response.json()
            assert payload["status"] == "success"
            rows = payload["data"]["rows"]
            assert len(rows) == 1
            row = rows[0]
            assert "id_card" not in row
            assert row["enterprise_wechat_user_id"] == "anhao"
            assert row["username"] == "anhao"
            assert row["position"] == "商务助理"
            assert row["emp_status"] == 3
            assert row["departments"][0]["external_dept_id"] == "50"
            assert row["primary_external_dept_id"] == "50"
        finally:
            engine.dispose()
