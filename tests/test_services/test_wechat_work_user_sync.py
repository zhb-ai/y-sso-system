"""按 userid 同步一名企微成员，并在未绑定账号时创建用户。"""

import logging
from types import SimpleNamespace

import pytest

from app.domain.wechat_work.sync_service import WechatWorkSyncService


class SyncState:
    """保存本次测试里的员工、部门和任职关系。"""

    rel = None
    employee = None
    depts = []
    dept_rels = []


class QueryColumn:
    """让过滤表达式可以求值。查询本身不使用该结果。"""

    def __eq__(self, other):
        return True


class ChainQuery:
    """可链式调用的内存查询。"""

    def __init__(self, first_row=None, rows=None):
        self._first = first_row
        self._rows = list(rows or [])

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._first

    def all(self):
        return list(self._rows)

    def delete(self):
        return 0


class RelQuery(ChainQuery):
    """读取当前测试保存的组织关系。"""

    def __init__(self):
        super().__init__()

    def first(self):
        return SyncState.rel


class EmployeeModel:
    """可构造、可按 ID 取回的员工模型。"""

    query = ChainQuery()

    def __init__(self, **kwargs):
        self.id = 11
        self.user_id = None
        self.primary_dept_id = None
        self.enterprise_wechat_openid = None
        self.name = ""
        self.__dict__.update(kwargs)
        self.id = kwargs.get("id", 11)
        SyncState.employee = self

    def save(self, commit=True):
        SyncState.employee = self
        return self

    @staticmethod
    def get(employee_id):
        employee = SyncState.employee
        if employee is not None and employee.id == employee_id:
            return employee
        return None


class EmpOrgRelModel:
    """员工与组织的关系。"""

    query = RelQuery()
    org_id = QueryColumn()
    external_user_id = QueryColumn()
    employee_id = QueryColumn()

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def save(self, commit=True):
        SyncState.rel = self
        return self


class DepartmentModel:
    """可补建的部门。查询结果来自本轮已创建的部门。"""

    org_id = QueryColumn()
    external_dept_id = QueryColumn()
    _next_id = 100

    def __init__(self, **kwargs):
        DepartmentModel._next_id += 1
        self.id = DepartmentModel._next_id
        self.parent_id = None
        self.__dict__.update(kwargs)
        if "id" not in kwargs:
            self.id = DepartmentModel._next_id
        SyncState.depts.append(self)

    def update_path_and_level(self):
        return None

    def save(self, commit=True):
        return self

    class query:
        @staticmethod
        def filter(*args, **kwargs):
            return DepartmentModel.query

        @staticmethod
        def all():
            return list(SyncState.depts)

        @staticmethod
        def first():
            return SyncState.depts[0] if SyncState.depts else None


class EmpDeptRelModel:
    """员工部门关系。没有部门时不会新增。"""

    query = ChainQuery(rows=[])
    employee_id = QueryColumn()
    dept_id = QueryColumn()

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        SyncState.dept_rels.append(self)

    def save(self, commit=True):
        return self


def _member_detail(userid="lisi", name="李四"):
    return {
        "userid": userid,
        "name": name,
        "department": [1],
        "status": 1,
        "email": f"{userid}@example.com",
    }


def _build_service():
    client = SimpleNamespace(
        get_user=lambda user_id: _member_detail(user_id),
        convert_userid_to_openid=lambda user_id: f"openid-{user_id}",
    )
    org_models = SimpleNamespace(
        Organization=object,
        Department=DepartmentModel,
        Employee=EmployeeModel,
        EmployeeOrgRel=EmpOrgRelModel,
        EmployeeDeptRel=EmpDeptRelModel,
    )
    return WechatWorkSyncService(client, org_models)


class TestSyncUserByUserid:
    """单成员同步会写员工，并按是否已有账号决定是否创建用户。"""

    def setup_method(self):
        SyncState.rel = None
        SyncState.employee = None
        SyncState.depts = []
        SyncState.dept_rels = []

    def test_creates_account_when_employee_is_not_bound(self, monkeypatch):
        """新成员没有 user_id 时，同步后创建系统用户。"""
        service = _build_service()
        service._cached_departments = [{"stale": True}]
        service._cached_employees = [{"stale": True}]
        created = {}

        class FakeAccountService:
            def __init__(self, employee_model):
                created["model"] = employee_model

            def create_account_for_employee(self, employee_id):
                created["employee_id"] = employee_id
                return {"user_id": 8, "username": "lisi"}

        monkeypatch.setattr(
            "app.services.employee_app.EmployeeAccountService",
            FakeAccountService,
        )

        result = service.sync_user_by_userid(SimpleNamespace(id=1), "lisi")

        assert result["is_new_employee"] is True
        assert result["account_created"] is True
        assert result["user_id"] == 8
        assert result["username"] == "lisi"
        assert result["employee"].name == "李四"
        assert result["employee"].user_id == 8
        assert created["employee_id"] == 11
        assert service._cached_departments is None
        assert service._cached_employees is None
        lock = service._get_lock(1)
        assert lock.acquire(blocking=False)
        lock.release()

    def test_skips_account_creation_when_user_is_already_bound(self, monkeypatch):
        """员工已经关联用户时，不重复创建账号。"""
        service = _build_service()
        service._cached_departments = [{"stale": True}]
        service._cached_employees = [{"stale": True}]
        employee = SimpleNamespace(
            id=21,
            user_id=5,
            name="王五",
            primary_dept_id=None,
            enterprise_wechat_user_id="wangwu",
            enterprise_wechat_openid="openid-wangwu",
            email="wangwu@example.com",
            avatar=None,
            gender=0,
            mobile=None,
            id_card=None,
            save=lambda commit=True: None,
        )
        SyncState.employee = employee
        SyncState.rel = SimpleNamespace(
            employee_id=21,
            emp_no=None,
            position=None,
            enterprise_wechat_openid=None,
            save=lambda commit=True: None,
        )

        def _forbid_create(*args, **kwargs):
            raise AssertionError("已绑定用户时不应创建账号")

        monkeypatch.setattr(
            "app.services.employee_app.EmployeeAccountService",
            _forbid_create,
        )
        monkeypatch.setattr(
            "app.domain.auth.model.user.User.get",
            staticmethod(lambda user_id: SimpleNamespace(id=user_id, username="wangwu")),
        )
        service.client.get_user = lambda user_id: _member_detail("wangwu", "王五")

        result = service.sync_user_by_userid(SimpleNamespace(id=1), "wangwu")

        assert result["is_new_employee"] is False
        assert result["account_created"] is False
        assert result["user_id"] == 5
        assert result["username"] == "wangwu"
        assert service._cached_departments is None
        assert service._cached_employees is None

    def test_blank_userid_raises_before_sync(self, monkeypatch):
        """空 userid 直接拒绝，不调用企微接口。"""
        service = _build_service()
        service._cached_departments = [{"stale": True}]
        service._cached_employees = [{"stale": True}]
        called = {"count": 0}

        def _get_user(user_id):
            called["count"] += 1
            return _member_detail(user_id)

        service.client.get_user = _get_user

        with pytest.raises(ValueError, match="userid"):
            service.sync_user_by_userid(SimpleNamespace(id=1), "  ")

        assert called["count"] == 0
        assert service._cached_departments == [{"stale": True}]
        assert service._cached_employees == [{"stale": True}]

    def test_lock_timeout_rejects_sync(self, monkeypatch):
        """组织同步锁 60 秒内拿不到时，拒绝本次同步。"""
        service = _build_service()
        busy = SimpleNamespace(
            acquire=lambda blocking=True, timeout=None: False,
            release=lambda: (_ for _ in ()).throw(AssertionError("未拿到锁不应释放")),
        )
        seen = {}

        def _lock(org_id):
            seen["org_id"] = org_id
            seen["timeout"] = None

            def _acquire(blocking=True, timeout=None):
                seen["blocking"] = blocking
                seen["timeout"] = timeout
                return False

            busy.acquire = _acquire
            return busy

        monkeypatch.setattr(WechatWorkSyncService, "_get_lock", staticmethod(_lock))

        with pytest.raises(ValueError, match="同步正在进行中"):
            service.sync_user_by_userid(SimpleNamespace(id=4), "lisi")

        assert seen["org_id"] == 4
        assert seen["blocking"] is True
        assert seen["timeout"] == 60

    def _allow_account(self, monkeypatch):
        class FakeAccountService:
            def __init__(self, employee_model):
                self.employee_model = employee_model

            def create_account_for_employee(self, employee_id):
                return {"user_id": 8, "username": "lisi"}

        monkeypatch.setattr(
            "app.services.employee_app.EmployeeAccountService",
            FakeAccountService,
        )

    def test_missing_department_is_created_and_linked(self, monkeypatch):
        """本地没有成员所属部门时，按企微部门详情补建并写入任职关系。"""
        service = _build_service()
        self._allow_account(monkeypatch)
        service.client.get_user = lambda user_id: {
            **_member_detail(user_id, "李四"),
            "department": [1, 2],
            "main_department": 2,
        }
        seen = {}

        def _get_department(dept_id):
            seen["dept_id"] = dept_id
            return [
                {"id": 2, "name": "研发部", "parentid": 1, "order": 3},
                {"id": 9, "name": "下级组", "parentid": 2, "order": 1},
            ]

        service.client.get_department = _get_department

        result = service.sync_user_by_userid(SimpleNamespace(id=1), "lisi")

        assert seen["dept_id"] == 2
        assert len(SyncState.depts) == 1
        dept = SyncState.depts[0]
        assert dept.external_dept_id == "2"
        assert dept.name == "研发部"
        assert dept.org_id == 1
        assert len(SyncState.dept_rels) == 1
        assert SyncState.dept_rels[0].employee_id == result["employee"].id
        assert SyncState.dept_rels[0].dept_id == dept.id
        assert SyncState.dept_rels[0].external_dept_id == "2"
        assert result["employee"].primary_dept_id == dept.id
        assert result["account_created"] is True
        assert result["username"] == "lisi"

    def test_department_lookup_failure_still_creates_user(self, monkeypatch, caplog):
        """读取部门详情失败时，仍创建员工和系统用户，不建立部门任职。"""
        service = _build_service()
        self._allow_account(monkeypatch)
        service.client.get_user = lambda user_id: {
            **_member_detail(user_id, "李四"),
            "department": [2],
            "main_department": 2,
        }

        def _get_department(dept_id):
            raise ValueError("获取企业微信部门详情失败")

        service.client.get_department = _get_department
        caplog.set_level(logging.WARNING, logger="app.domain.wechat_work.sync_service")

        result = service.sync_user_by_userid(SimpleNamespace(id=1), "lisi")

        assert result["is_new_employee"] is True
        assert result["account_created"] is True
        assert result["employee"].name == "李四"
        assert SyncState.depts == []
        assert SyncState.dept_rels == []
        assert result["employee"].primary_dept_id is None
        assert "补建部门失败" in caplog.text
        assert "external_dept_id=2" in caplog.text
