"""下游员工同步查询测试。"""

import pytest

from yweb.orm import BaseModel, init_database

from app.domain.auth.model.user import User
from app.models_registry import ensure_dynamic_models
from app.services.org_sync import ensure_employee_for_sync, list_employees_for_sync


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
    """让创建用户能读到角色模型。本进程若尚未初始化认证，只在本测试内挂上。"""
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


class TestEnsureEmployeeForSync:
    """按企微 userid 确保员工：已有数据不请求企微，缺失时才创建。"""

    def test_blank_userid_raises(self, org_models):
        """去掉空白后为空时拒绝，并且不创建员工"""
        organization = _seed_company(org_models)
        with pytest.raises(ValueError, match="不能为空"):
            ensure_employee_for_sync(
                org_models,
                org_id=organization.id,
                enterprise_wechat_user_id="   ",
            )
        assert org_models.Employee.query.count() == 0

    def test_existing_employee_and_user_skips_wechat_and_writes(
        self, org_models, monkeypatch
    ):
        """员工和用户都在时，不请求企微，也不创建账号"""

        class RejectAccountService:
            def __init__(self, employee_model):
                pass

            def create_account_for_employee(self, employee_id, username=None):
                raise AssertionError("已有用户时不应创建账号")

        _forbid_wechat(monkeypatch)
        monkeypatch.setattr(
            "app.services.org_sync.EmployeeAccountService",
            RejectAccountService,
        )
        organization = _seed_company(org_models)
        dept = _add_dept(org_models, organization, name="开发组", external_dept_id="50")
        user = _add_user(username="anhao", phone="13800001111", name="安浩")
        employee = _add_employee(
            org_models,
            organization,
            name="开发组-安浩-商务助理",
            wecom="anhao",
            position="商务助理",
            user=user,
            depts=[dept],
            mobile="13800001111",
            email="anhao@example.com",
        )
        user_count = User.query.count()

        result = ensure_employee_for_sync(
            org_models,
            org_id=organization.id,
            enterprise_wechat_user_id="  anhao  ",
        )

        assert result.existed is True
        assert User.query.count() == user_count
        reloaded = org_models.Employee.get(employee.id)
        assert reloaded.user_id == user.id
        assert reloaded.name == "开发组-安浩-商务助理"
        row = result.record
        assert row.enterprise_wechat_user_id == "anhao"
        assert row.username == "anhao"
        assert row.name == "开发组-安浩-商务助理"
        assert row.email == "anhao@example.com"
        assert row.mobile == "13800001111"
        assert row.position == "商务助理"
        assert row.emp_status == 3
        assert row.account_status == 1
        assert row.is_active is True
        assert row.primary_external_dept_id == "50"
        assert row.departments[0].external_dept_id == "50"
        assert not hasattr(row, "id_card")

    def test_employee_without_user_creates_account_without_wechat(
        self, org_models, monkeypatch
    ):
        """员工在、用户不在时只创建用户，不请求企微，结果里没有明文密码"""
        _forbid_wechat(monkeypatch)
        _bind_account_auth(monkeypatch)
        sentinel = _fixed_password(monkeypatch)
        organization = _seed_company(org_models, code="ensure-account")
        dept = _add_dept(org_models, organization, name="开发组", external_dept_id="50")
        employee = _add_employee(
            org_models,
            organization,
            name="陈五",
            wecom="chenwu",
            position="助理",
            depts=[dept],
            mobile="13800003333",
            email="chenwu@example.com",
        )
        employee_count = org_models.Employee.query.count()

        result = ensure_employee_for_sync(
            org_models,
            org_id=organization.id,
            enterprise_wechat_user_id="chenwu",
        )

        assert result.existed is True
        assert org_models.Employee.query.count() == employee_count
        reloaded = org_models.Employee.get(employee.id)
        assert reloaded.user_id is not None
        assert reloaded.name == "陈五"
        assert reloaded.enterprise_wechat_user_id == "chenwu"
        row = result.record
        assert row.username == "chenwu"
        assert row.user_id == reloaded.user_id
        assert row.account_status == 1
        assert row.is_active is True
        assert row.mobile == "13800003333"
        assert row.position == "助理"
        assert sentinel not in str(row)

    def test_finds_employee_by_wechat_column_when_rel_userid_differs(
        self, org_models, monkeypatch
    ):
        """关系表 external_user_id 不一致时，仍按员工表企微 userid 命中，且不请求企微"""
        _forbid_wechat(monkeypatch)
        organization = _seed_company(org_models, code="ensure-column")
        user = _add_user(username="zhangsan", name="张三")
        employee = _add_employee(
            org_models,
            organization,
            name="张三",
            wecom="zhangsan",
            user=user,
        )
        rel = org_models.EmployeeOrgRel.query.filter_by(employee_id=employee.id).first()
        rel.external_user_id = "legacy-id"
        rel.save(commit=True)

        result = ensure_employee_for_sync(
            org_models,
            org_id=organization.id,
            enterprise_wechat_user_id="zhangsan",
        )

        assert result.existed is True
        assert result.record.employee_id == employee.id
        assert result.record.username == "zhangsan"

    def test_missing_employee_syncs_from_wechat_and_returns_row(
        self, org_models, monkeypatch
    ):
        """员工和用户都不在时，请求企微并创建后返回同步行"""
        _bind_account_auth(monkeypatch)
        sentinel = _fixed_password(monkeypatch)
        organization = _seed_company(org_models, code="ensure-wechat")
        _add_dept(org_models, organization, name="开发组", external_dept_id="50")
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

        result = ensure_employee_for_sync(
            org_models,
            org_id=organization.id,
            enterprise_wechat_user_id="  lisi  ",
        )

        assert client.get_user_calls == ["lisi"]
        assert result.existed is False
        row = result.record
        assert row.enterprise_wechat_user_id == "lisi"
        assert row.username == "lisi"
        assert row.name == "李四"
        assert row.email == "lisi@example.com"
        assert row.mobile == "13800002222"
        assert row.position == "开发"
        assert row.emp_status == 3
        assert row.account_status == 1
        assert row.is_active is True
        assert row.user_id is not None
        assert row.primary_external_dept_id == "50"
        assert row.departments[0].external_dept_id == "50"
        assert sentinel not in str(row)
        assert org_models.Employee.query.count() == 1
        assert User.query.filter_by(username="lisi").count() == 1

    def test_wechat_failure_does_not_persist(self, org_models, monkeypatch):
        """企微读取失败时不写入员工或用户"""
        organization = _seed_company(org_models, code="ensure-wechat-fail")
        client = RecordingWechatClient(
            error=ValueError("获取企业微信成员详情失败: userid=lisi")
        )
        _use_wechat_client(monkeypatch, client)

        with pytest.raises(ValueError, match="获取企业微信成员详情失败: userid=lisi"):
            ensure_employee_for_sync(
                org_models,
                org_id=organization.id,
                enterprise_wechat_user_id="lisi",
            )

        assert client.get_user_calls == ["lisi"]
        assert org_models.Employee.query.count() == 0
        assert User.query.count() == 0

    def test_missing_contact_secret_does_not_persist(self, org_models):
        """组织未配置通讯录 Secret 时拒绝，并且不创建员工"""
        organization = org_models.Organization(
            name="测试组织",
            code="ensure-no-secret",
            is_active=True,
            external_corp_id="ww-test",
        )
        organization.add(True)

        with pytest.raises(ValueError, match="未配置企业微信 corp_secret"):
            ensure_employee_for_sync(
                org_models,
                org_id=organization.id,
                enterprise_wechat_user_id="lisi",
            )

        assert org_models.Employee.query.count() == 0

    def test_taken_username_rejects_before_wechat(self, org_models, monkeypatch):
        """用户名已被别人占用时返回服务错误文本，不请求企微，不新建员工"""
        _forbid_wechat(monkeypatch)
        organization = _seed_company(org_models, code="ensure-name-taken")
        _add_user(username="lisi", name="别人")

        with pytest.raises(ValueError, match="用户名已存在: lisi"):
            ensure_employee_for_sync(
                org_models,
                org_id=organization.id,
                enterprise_wechat_user_id="lisi",
            )

        assert org_models.Employee.query.count() == 0

    def test_employee_in_other_org_is_not_created_again(self, org_models, monkeypatch):
        """员工表已有该企微 userid 但不属于当前组织时，不请求企微，也不再建一名员工"""
        _forbid_wechat(monkeypatch)
        current_org = _seed_company(org_models, code="ensure-current")
        other_org = _seed_company(org_models, code="ensure-other")
        _add_employee(org_models, other_org, name="张三", wecom="zhangsan")

        with pytest.raises(ValueError, match="不属于组织"):
            ensure_employee_for_sync(
                org_models,
                org_id=current_org.id,
                enterprise_wechat_user_id="zhangsan",
            )

        assert org_models.Employee.query.count() == 1
