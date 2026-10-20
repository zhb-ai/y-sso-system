"""按用户名查询花名册的 HTTP 契约。"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.hr_roster import create_hr_roster_router


def _client():
    app = FastAPI()
    app.include_router(create_hr_roster_router(employee_model=object), prefix="/api/v1")
    return TestClient(app)


class TestHrRosterApi:
    """接口按用户名返回已保存的花名册，找不到时返回 404。"""

    def test_returns_saved_roster(self, monkeypatch):
        monkeypatch.setattr(
            "app.api.v1.hr_roster.get_hr_roster_by_username",
            lambda employee_model, username: {
                "username": username,
                "employee_id": 9,
                "hr_roster": {"userid": "wecom-id", "groups": []},
            },
        )

        response = _client().get("/api/v1/employees/hr-roster", params={"username": "luxiaopeng"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["data"]["username"] == "luxiaopeng"
        assert payload["data"]["employee_id"] == 9
        assert payload["data"]["hr_roster"]["userid"] == "wecom-id"

    def test_missing_user_returns_404(self, monkeypatch):
        def raise_missing(employee_model, username):
            raise ValueError(f"用户不存在: {username}")

        monkeypatch.setattr(
            "app.api.v1.hr_roster.get_hr_roster_by_username",
            raise_missing,
        )

        response = _client().get("/api/v1/employees/hr-roster", params={"username": "nobody"})

        assert response.status_code == 404
        assert "用户不存在" in response.json()["message"]
