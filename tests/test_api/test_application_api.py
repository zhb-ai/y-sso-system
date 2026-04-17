"""应用管理 API 测试"""

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.application import create_application_router
from app.domain.application.services import ApplicationService


class TestApplicationApi:
    """应用管理 API 行为测试"""

    def test_create_application_accepts_client_type(self, monkeypatch):
        """创建应用时应透传并返回 client_type"""

        captured = {}

        def _create_application(
            self,
            name,
            code,
            description=None,
            redirect_uris=None,
            allowed_ip_cidrs=None,
            logo_url=None,
            client_type="confidential",
        ):
            captured["client_type"] = client_type
            captured["allowed_ip_cidrs"] = allowed_ip_cidrs
            return SimpleNamespace(
                id=1,
                name=name,
                code=code,
                description=description,
                client_id="generated-client-id",
                client_secret="generated-client-secret",
                client_type=client_type,
                redirect_uris=redirect_uris or [],
                allowed_ip_cidrs=allowed_ip_cidrs or [],
                logo_url=logo_url,
                is_active=True,
                created_at=None,
                updated_at=None,
            )

        monkeypatch.setattr(
            ApplicationService,
            "create_application",
            _create_application,
            raising=False,
        )

        app = FastAPI()
        app.include_router(create_application_router(), prefix="/api/v1")
        client = TestClient(app)

        response = client.post(
            "/api/v1/applications/create",
            json={
                "name": "Public App",
                "code": "public_app",
                "description": "公开客户端",
                "redirect_uris": ["http://localhost/callback"],
                "allowed_ip_cidrs": ["203.0.113.10", "198.51.100.0/24"],
                "client_type": "public",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert captured["client_type"] == "public"
        assert captured["allowed_ip_cidrs"] == ["203.0.113.10", "198.51.100.0/24"]
        assert payload["data"]["client_type"] == "public"
        assert payload["data"]["allowed_ip_cidrs"] == ["203.0.113.10", "198.51.100.0/24"]

    def test_update_application_accepts_client_type(self, monkeypatch):
        """更新应用时应透传 client_type"""

        captured = {}

        def _update_application(self, app_id, **kwargs):
            captured["app_id"] = app_id
            captured["kwargs"] = kwargs
            return SimpleNamespace(
                id=app_id,
                name="Data Formulator",
                code="data_formulator",
                description="updated",
                client_id="client-id-123",
                client_secret="",
                client_type=kwargs.get("client_type", "confidential"),
                redirect_uris=kwargs.get("redirect_uris", []),
                allowed_ip_cidrs=kwargs.get("allowed_ip_cidrs", []),
                logo_url=kwargs.get("logo_url"),
                is_active=True,
                created_at=None,
                updated_at=None,
            )

        monkeypatch.setattr(
            ApplicationService,
            "update_application",
            _update_application,
            raising=False,
        )

        app = FastAPI()
        app.include_router(create_application_router(), prefix="/api/v1")
        client = TestClient(app)

        response = client.post(
            "/api/v1/applications/update",
            params={"app_id": 7},
            json={
                "name": "Data Formulator",
                "description": "updated",
                "redirect_uris": ["http://localhost/callback"],
                "allowed_ip_cidrs": ["203.0.113.10/32"],
                "client_type": "public",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert captured["app_id"] == 7
        assert captured["kwargs"]["client_type"] == "public"
        assert captured["kwargs"]["allowed_ip_cidrs"] == ["203.0.113.10/32"]
        assert payload["data"]["client_type"] == "public"
        assert payload["data"]["allowed_ip_cidrs"] == ["203.0.113.10/32"]

    def test_get_application_secret_returns_current_secret(self, monkeypatch):
        """应返回指定应用当前保存的客户端密钥"""
        monkeypatch.setattr(
            ApplicationService,
            "get_application_secret",
            lambda self, app_id: SimpleNamespace(
                id=app_id,
                name="Data Formulator",
                code="data_formulator",
                client_id="client-id-123",
                client_secret="secret-value-456",
            ),
            raising=False,
        )

        app = FastAPI()
        app.include_router(create_application_router(), prefix="/api/v1")
        client = TestClient(app)

        response = client.get("/api/v1/applications/secret", params={"app_id": 7})

        assert response.status_code == 200
        payload = response.json()
        assert payload["data"]["id"] == 7
        assert payload["data"]["client_id"] == "client-id-123"
        assert payload["data"]["client_secret"] == "secret-value-456"

    def test_get_application_secret_returns_not_found_when_missing(self, monkeypatch):
        """应用不存在时应返回 404"""

        def _raise_not_found(self, app_id):
            raise ValueError(f"应用不存在: {app_id}")

        monkeypatch.setattr(
            ApplicationService,
            "get_application_secret",
            _raise_not_found,
            raising=False,
        )

        app = FastAPI()
        app.include_router(create_application_router(), prefix="/api/v1")
        client = TestClient(app)

        response = client.get("/api/v1/applications/secret", params={"app_id": 404})

        assert response.status_code == 404
        assert response.json()["message"] == "应用不存在: 404"
