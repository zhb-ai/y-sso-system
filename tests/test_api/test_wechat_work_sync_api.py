"""企业微信手动同步 API 测试"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from yweb.organization import ExternalSource, SyncResult

from app.api.v1.wechat_work import create_wechat_work_router


def _wechat_org(org_id=1, corp_id="ww-test", name="测试组织"):
    """构造一个已绑定企微的组织。"""
    return SimpleNamespace(
        id=org_id,
        name=name,
        external_source=ExternalSource.WECHAT_WORK.value,
        external_corp_id=corp_id,
    )


class FakeOrganization:
    """测试用组织模型，避免 pytest 误识别为测试类。"""

    @staticmethod
    def get(org_id):
        if org_id == 1:
            return _wechat_org()
        return None


def _build_client():
    org_models = SimpleNamespace(Organization=FakeOrganization)
    app = FastAPI()
    app.include_router(create_wechat_work_router(org_models), prefix="/api/v1")
    return TestClient(app)


class TestWechatWorkManualSyncApi:
    """手动同步接口应把同步错误返回给前端"""

    def test_manual_sync_exposes_partial_failures_in_msg_details(self, monkeypatch):
        """部分失败时，响应必须带上可定位问题的错误详情"""
        sync_result = SyncResult()
        sync_result.add_error(
            "同步员工失败: (pymysql.err.DataError) (1406, "
            "\"Data too long for column 'id_card' at row 1\")"
        )
        sync_result.finish()

        mock_service = MagicMock()
        mock_service.sync_from_external.return_value = sync_result
        monkeypatch.setattr(
            "app.domain.wechat_work.client.WechatWorkClient.from_organization",
            lambda org: MagicMock(),
        )
        monkeypatch.setattr(
            "app.domain.wechat_work.sync_service.WechatWorkSyncService",
            lambda client, org_models=None: mock_service,
        )

        response = _build_client().post(
            "/api/v1/wechat-work/sync/manual",
            json={"org_id": 1},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "warning"
        assert payload["msg_details"], "部分失败时 msg_details 不能为空"
        assert any("id_card" in item for item in payload["msg_details"])
        assert any("id_card" in item for item in payload["data"]["errors"])

    def test_manual_sync_success_keeps_empty_details(self, monkeypatch):
        """全部成功时不应伪装成警告"""
        sync_result = SyncResult()
        sync_result.created_count = 2
        sync_result.finish()

        mock_service = MagicMock()
        mock_service.sync_from_external.return_value = sync_result
        monkeypatch.setattr(
            "app.domain.wechat_work.client.WechatWorkClient.from_organization",
            lambda org: MagicMock(),
        )
        monkeypatch.setattr(
            "app.domain.wechat_work.sync_service.WechatWorkSyncService",
            lambda client, org_models=None: mock_service,
        )

        response = _build_client().post(
            "/api/v1/wechat-work/sync/manual",
            json={"org_id": 1},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "success"
        assert payload["msg_details"] == []
        assert payload["data"]["created_count"] == 2
        assert payload["data"]["errors"] == []


class TestWechatWorkPlaintextCallbackClosed:
    """明文回调已关闭，请求不能进入成员同步。"""

    def test_callback_routes_are_not_registered(self):
        """明文回调路径不再挂到路由器上。"""
        app = FastAPI()
        app.include_router(
            create_wechat_work_router(SimpleNamespace(Organization=FakeOrganization)),
            prefix="/api/v1",
        )
        paths = {getattr(route, "path", "") for route in app.routes}
        assert "/api/v1/wechat-work/callback" not in paths
        assert "/api/v1/wechat-work/callback/{org_id}" not in paths

    def test_post_callback_returns_404_and_does_not_sync(self, monkeypatch):
        """POST 明文回调返回 404，并且不调用成员同步。"""
        service = MagicMock()
        monkeypatch.setattr(
            "app.domain.wechat_work.client.WechatWorkClient.from_organization",
            lambda org: MagicMock(),
        )
        monkeypatch.setattr(
            "app.domain.wechat_work.sync_service.WechatWorkSyncService",
            lambda client, org_models=None: service,
        )
        client = _build_client()

        response = client.post(
            "/api/v1/wechat-work/callback",
            json={"userid": "lisi", "ToUserName": "wwa45051e5c8780853"},
        )
        by_org = client.post(
            "/api/v1/wechat-work/callback/1",
            json={"userid": "lisi"},
        )

        assert response.status_code == 404
        assert by_org.status_code == 404
        service.sync_user_by_userid.assert_not_called()
        service.handle_create_department.assert_not_called()
