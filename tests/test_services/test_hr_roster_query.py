"""按 user.username 读取花名册。"""

import pytest

from app.services.hr_roster_app import get_hr_roster_by_username


class _Query:
    def __init__(self, employee):
        self.employee = employee

    def filter(self, *args):
        return self

    def first(self):
        return self.employee


class _EmployeeModel:
    user_id = object()

    def __init__(self, employee):
        self.employee = employee

    @property
    def query(self):
        return _Query(self.employee)


class _User:
    def __init__(self, username, user_id):
        self.username = username
        self.id = user_id


class TestGetHrRosterByUsername:
    """查询必须走用户名到员工的关联，而不是把用户名当成企微 userid。"""

    def test_returns_roster_of_the_linked_employee(self, monkeypatch):
        roster = {"userid": "wecom-id", "groups": [{"group_name": "个人信息"}]}
        employee = type("EmployeeRow", (), {"id": 9, "hr_roster": roster})()
        monkeypatch.setattr(
            "app.services.hr_roster_app.User.get_by_username",
            lambda username: _User(username, 3),
        )

        found = get_hr_roster_by_username(_EmployeeModel(employee), "luxiaopeng")

        assert found["username"] == "luxiaopeng"
        assert found["employee_id"] == 9
        assert found["hr_roster"]["userid"] == "wecom-id"

    def test_missing_user_is_rejected(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.hr_roster_app.User.get_by_username",
            lambda username: None,
        )

        with pytest.raises(ValueError, match="用户不存在"):
            get_hr_roster_by_username(_EmployeeModel(None), "nobody")

    def test_user_without_employee_is_rejected(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.hr_roster_app.User.get_by_username",
            lambda username: _User(username, 3),
        )

        with pytest.raises(ValueError, match="未关联员工"):
            get_hr_roster_by_username(_EmployeeModel(None), "luxiaopeng")

    def test_employee_without_roster_is_rejected(self, monkeypatch):
        employee = type("EmployeeRow", (), {"id": 9, "hr_roster": None})()
        monkeypatch.setattr(
            "app.services.hr_roster_app.User.get_by_username",
            lambda username: _User(username, 3),
        )

        with pytest.raises(ValueError, match="还没有花名册数据"):
            get_hr_roster_by_username(_EmployeeModel(employee), "luxiaopeng")
