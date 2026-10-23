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


class RecordingWechatClient:
    """记录 get_user 调用，不访问企业微信。"""

    def __init__(self, detail=None, error=None):
        self.get_user_calls = []
        self.detail = dict(detail or {})
        self.error = error

    def get_user(self, user_id):
        self.get_user_calls.append(user_id)
        if self.error is not None:
            raise self.error
        payload = dict(self.detail)
        payload.setdefault("userid", user_id)
        return payload

    def convert_userid_to_openid(self, user_id):
        return f"openid-{user_id}"

    def get_department(self, dept_id):
        return {"id": dept_id, "name": "开发组", "parentid": 1, "order": 0}


def _forbid_wechat(monkeypatch):
    def _raise(org):
        raise AssertionError("不应请求企微")

    monkeypatch.setattr(
        "app.domain.wechat_work.client.WechatWorkClient.from_organization",
        _raise,
    )


def _use_wechat_client(monkeypatch, client):
    monkeypatch.setattr(
        "app.domain.wechat_work.client.WechatWorkClient.from_organization",
        lambda org: client,
    )


def _bind_account_auth(monkeypatch):
    from app.api import dependencies
    from app.models_registry import ensure_dynamic_models

    if dependencies.auth is None:
        monkeypatch.setattr(
            dependencies,
            "auth",
            ensure_dynamic_models()._auth,
            raising=False,
        )


def _fixed_password(monkeypatch):
    sentinel = "PwSentinel9!"
    monkeypatch.setattr(
        "app.services.employee_app.generate_strong_password",
        lambda *args, **kwargs: sentinel,
    )
    return sentinel


def _post_ensure(org_models, payload):
    return _client(org_models).post(
        "/api/v1/org/sync/employees/ensure",
        json=payload,
    )


_ROW_FIELDS = (
    "enterprise_wechat_user_id",
    "username",
    "name",
    "email",
    "mobile",
    "departments",
    "primary_external_dept_id",
    "position",
    "emp_status",
    "account_status",
    "is_active",
    "existed",
)


def _assert_flat_sync_row(data):
    assert isinstance(data, dict)
    assert "rows" not in data
    for key in _ROW_FIELDS:
        assert key in data
    for secret_key in ("id_card", "password", "raw_password", "password_hash"):
        assert secret_key not in data


class TestEnsureSyncEmployeeApi:
    """POST /org/sync/employees/ensure 返回单行，失败时沿用服务错误文本。"""

    def test_blank_userid_returns_bad_request(self):
        """userid 为空或只有空白时返回 400"""
        org_models, engine = _setup()
        try:
            empty = _post_ensure(
                org_models,
                {"org_id": 1, "enterprise_wechat_user_id": ""},
            )
            blank = _post_ensure(
                org_models,
                {"org_id": 1, "enterprise_wechat_user_id": "   "},
            )
            assert empty.status_code == 400
            assert blank.status_code == 400
            assert "不能为空" in empty.json()["message"]
            assert "不能为空" in blank.json()["message"]
            assert org_models.Employee.query.count() == 0
        finally:
            engine.dispose()

    def test_existing_employee_returns_one_row_without_wechat(self, monkeypatch):
        """已有员工和用户时，data 是同步行本身，并且不请求企微"""
        _forbid_wechat(monkeypatch)
        org_models, engine = _setup()
        try:
            organization = org_models.Organization(
                name="洋帆", code="ensure-api", is_active=True
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
                email="anhao@example.com",
                phone="13800001111",
            )
            user.add(True)
            employee = org_models.Employee(
                name="开发组-安浩-商务助理",
                gender=0,
                is_senior=False,
                user_id=user.id,
                enterprise_wechat_user_id="anhao",
                email="anhao@example.com",
                mobile="13800001111",
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

            response = _post_ensure(
                org_models,
                {
                    "org_id": organization.id,
                    "enterprise_wechat_user_id": "anhao",
                },
            )
            assert response.status_code == 200
            payload = response.json()
            assert payload["status"] == "success"
            data = payload["data"]
            _assert_flat_sync_row(data)
            assert data["existed"] is True
            assert data["enterprise_wechat_user_id"] == "anhao"
            assert data["username"] == "anhao"
            assert data["name"] == "开发组-安浩-商务助理"
            assert data["email"] == "anhao@example.com"
            assert data["mobile"] == "13800001111"
            assert data["position"] == "商务助理"
            assert data["emp_status"] == 3
            assert data["account_status"] == 1
            assert data["is_active"] is True
            assert data["primary_external_dept_id"] == "50"
            assert data["departments"][0]["external_dept_id"] == "50"
        finally:
            engine.dispose()

    def test_employee_without_user_creates_account_and_hides_password(
        self, monkeypatch
    ):
        """只创建用户账号时不请求企微，响应正文不包含明文密码"""
        _forbid_wechat(monkeypatch)
        _bind_account_auth(monkeypatch)
        sentinel = _fixed_password(monkeypatch)
        org_models, engine = _setup()
        try:
            organization = org_models.Organization(
                name="洋帆", code="ensure-api-account", is_active=True
            )
            organization.add(True)
            employee = org_models.Employee(
                name="陈五",
                gender=0,
                is_senior=False,
                enterprise_wechat_user_id="chenwu",
                email="chenwu@example.com",
                mobile="13800003333",
            )
            employee.add(True)
            org_models.EmployeeOrgRel(
                employee_id=employee.id,
                org_id=organization.id,
                status=3,
                position="助理",
                external_user_id="chenwu",
            ).add(True)

            response = _post_ensure(
                org_models,
                {
                    "org_id": organization.id,
                    "enterprise_wechat_user_id": "chenwu",
                },
            )
            assert response.status_code == 200
            assert sentinel not in response.text
            data = response.json()["data"]
            _assert_flat_sync_row(data)
            assert data["existed"] is True
            assert data["username"] == "chenwu"
            assert data["account_status"] == 1
            assert data["is_active"] is True
            assert data["user_id"] is not None
            assert org_models.Employee.query.count() == 1
        finally:
            engine.dispose()

    def test_missing_employee_returns_row_after_wechat_sync(self, monkeypatch):
        """本地没有员工时调用 get_user，响应是新建后的同步行"""
        _bind_account_auth(monkeypatch)
        sentinel = _fixed_password(monkeypatch)
        org_models, engine = _setup()
        try:
            organization = org_models.Organization(
                name="洋帆", code="ensure-api-wechat", is_active=True
            )
            organization.add(True)
            org_models.Department(
                name="开发组",
                org_id=organization.id,
                level=1,
                sort_order=0,
                is_active=True,
                external_dept_id="50",
            ).add(True)
            client = RecordingWechatClient(
                detail={
                    "userid": "lisi",
                    "name": "李四",
                    "department": [50],
                    "main_department": 50,
                    "status": 1,
                    "email": "lisi@example.com",
                    "mobile": "13800002222",
                    "position": "开发",
                }
            )
            _use_wechat_client(monkeypatch, client)

            response = _post_ensure(
                org_models,
                {
                    "org_id": organization.id,
                    "enterprise_wechat_user_id": "lisi",
                },
            )
            assert response.status_code == 200, response.text
            assert sentinel not in response.text
            assert client.get_user_calls == ["lisi"]
            data = response.json()["data"]
            _assert_flat_sync_row(data)
            assert data["existed"] is False
            assert data["enterprise_wechat_user_id"] == "lisi"
            assert data["username"] == "lisi"
            assert data["name"] == "李四"
            assert data["email"] == "lisi@example.com"
            assert data["mobile"] == "13800002222"
            assert data["position"] == "开发"
            assert data["emp_status"] == 3
            assert data["departments"][0]["external_dept_id"] == "50"
            assert data["primary_external_dept_id"] == "50"
        finally:
            engine.dispose()

    def test_wechat_failure_returns_service_message_without_rows(self, monkeypatch):
        """企微失败时返回服务抛出的文本，并且不落库"""
        org_models, engine = _setup()
        try:
            organization = org_models.Organization(
                name="洋帆", code="ensure-api-fail", is_active=True
            )
            organization.add(True)
            client = RecordingWechatClient(
                error=ValueError("获取企业微信成员详情失败: userid=nobody")
            )
            _use_wechat_client(monkeypatch, client)

            response = _post_ensure(
                org_models,
                {
                    "org_id": organization.id,
                    "enterprise_wechat_user_id": "nobody",
                },
            )
            assert response.status_code == 400
            payload = response.json()
            assert payload["status"] == "error"
            assert payload["message"] == "获取企业微信成员详情失败: userid=nobody"
            assert client.get_user_calls == ["nobody"]
            assert org_models.Employee.query.count() == 0
            assert User.query.count() == 0
        finally:
            engine.dispose()
