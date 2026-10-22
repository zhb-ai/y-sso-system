"""企业微信手动同步与明文回调 API 测试"""

import logging
from pathlib import Path
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


class OrgField:
    """记录组织查询条件，避免 pytest 把辅助类当成测试类。"""

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return ("eq", self.name, other)


class OrgQuery:
    """按字段等值过滤内存中的组织行。"""

    def __init__(self, rows):
        self._rows = list(rows)

    def filter(self, *criteria):
        matched = []
        for row in self._rows:
            ok = True
            for item in criteria:
                if not isinstance(item, tuple) or len(item) != 3 or item[0] != "eq":
                    ok = False
                    break
                _, name, expected = item
                if getattr(row, name) != expected:
                    ok = False
                    break
            if ok:
                matched.append(row)
        return OrgQuery(matched)

    def all(self):
        return list(self._rows)

    def first(self):
        return self._rows[0] if self._rows else None


class OrgQueryFactory:
    """每次访问 query 都从当前组织列表重新开始。"""

    def __get__(self, obj, owner):
        rows = owner.rows
        if rows is None:
            rows = [_wechat_org()]
        return OrgQuery(rows)


class FakeOrganization:
    """测试用组织模型，避免 pytest 误识别为测试类。"""

    rows = None
    external_source = OrgField("external_source")
    external_corp_id = OrgField("external_corp_id")
    query = OrgQueryFactory()

    @staticmethod
    def get(org_id):
        rows = FakeOrganization.rows
        if rows is None:
            rows = [_wechat_org()]
        for row in rows:
            if row.id == org_id:
                return row
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


def _sync_result(name="李四", username="lisi", account_created=True):
    """同步服务返回给接口的成员结果。"""
    return {
        "employee": SimpleNamespace(id=9, name=name),
        "is_new_employee": True,
        "account_created": account_created,
        "user_id": 3,
        "username": username,
    }


def _install_member_sync(monkeypatch, result=None):
    """替换同步服务，记录实际同步的组织和 userid。"""
    calls = []
    service = MagicMock()

    def _sync(org, user_id):
        calls.append((org, user_id))
        return result or _sync_result()

    service.sync_user_by_userid.side_effect = _sync
    monkeypatch.setattr(
        "app.domain.wechat_work.client.WechatWorkClient.from_organization",
        lambda org: MagicMock(),
    )
    monkeypatch.setattr(
        "app.domain.wechat_work.sync_service.WechatWorkSyncService",
        lambda client, org_models=None: service,
    )
    return calls


class TestWechatWorkPlaintextCallback:
    """明文转发回调：记日志、识别组织、同步指定成员。"""

    def setup_method(self):
        FakeOrganization.rows = None

    def teardown_method(self):
        FakeOrganization.rows = None

    def test_callback_routes_do_not_require_manage_permission(self):
        """回调路由本身不挂管理权限依赖。"""
        app = FastAPI()
        app.include_router(
            create_wechat_work_router(SimpleNamespace(Organization=FakeOrganization)),
            prefix="/api/v1",
        )
        found = {
            route.path: route
            for route in app.routes
            if getattr(route, "path", "").startswith("/api/v1/wechat-work/callback")
        }
        assert "/api/v1/wechat-work/callback" in found
        assert "/api/v1/wechat-work/callback/{org_id}" in found
        assert found["/api/v1/wechat-work/callback"].dependencies == []
        assert found["/api/v1/wechat-work/callback/{org_id}"].dependencies == []

    def test_route_registry_excludes_callback_from_permission_scan(self):
        """权限注册表必须把明文回调标成公开接口。"""
        routes = (Path(__file__).resolve().parents[2] / "app" / "api" / "routes.py").read_text(encoding="utf-8")
        assert 'perm_registry.exclude("/api/v1/wechat-work/callback")' in routes

    def test_logs_raw_body_and_parsed_json(self, monkeypatch, caplog):
        """收到转发请求时，日志必须包含路径、query、Content-Type、原文和解析结果。"""
        FakeOrganization.rows = [_wechat_org(corp_id="ww-body")]
        _install_member_sync(monkeypatch)
        caplog.set_level(logging.INFO, logger="app.api.v1.wechat_work")
        raw = '{"id":"event-1","data":{"userid":"lisi"},"ToUserName":"ww-body"}'

        response = _build_client().post(
            "/api/v1/wechat-work/callback?from=gateway",
            content=raw.encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "success"
        assert payload["data"]["userid"] == "lisi"
        assert payload["data"]["username"] == "lisi"
        assert payload["data"]["account_created"] is True
        text = caplog.text
        assert "收到企微转发回调请求" in text
        assert "path=/api/v1/wechat-work/callback" in text
        assert "from" in text and "gateway" in text
        assert "application/json" in text
        assert raw in text
        assert "parsed_data=" in text
        assert "lisi" in text

    def test_nested_event_userid_uses_the_only_bound_org(self, monkeypatch):
        """没有 org_id 和 corp_id 时，唯一的企微组织可以自动命中。"""
        org = _wechat_org(org_id=7, corp_id="ww-only", name="唯一组织")
        FakeOrganization.rows = [org]
        calls = _install_member_sync(monkeypatch)

        response = _build_client().post(
            "/api/v1/wechat-work/callback",
            json={"event": {"UserID": "wangwu"}},
        )

        assert response.status_code == 200
        assert calls[0][0].id == 7
        assert calls[0][1] == "wangwu"
        assert response.json()["data"]["org_id"] == 7

    def test_xml_userid_and_corp_id_select_matching_org(self, monkeypatch):
        """解密后的 XML 用 UserID 和 ToUserName 定位成员与组织。"""
        FakeOrganization.rows = [
            _wechat_org(org_id=1, corp_id="ww-other"),
            _wechat_org(org_id=2, corp_id="ww-match", name="匹配组织"),
        ]
        calls = _install_member_sync(monkeypatch, _sync_result(name="王五", username="wangwu"))
        xml = (
            "<xml>"
            "<ToUserName><![CDATA[ww-match]]></ToUserName>"
            "<UserID><![CDATA[wangwu]]></UserID>"
            "</xml>"
        )

        response = _build_client().post(
            "/api/v1/wechat-work/callback",
            content=xml.encode("utf-8"),
            headers={"Content-Type": "text/xml"},
        )

        assert response.status_code == 200
        assert calls[0][0].id == 2
        assert calls[0][1] == "wangwu"
        assert response.json()["data"]["employee_name"] == "王五"

    def test_query_userid_is_used_when_body_omits_it(self, monkeypatch):
        """正文没有成员字段时，从 query 的 UserID 读取。"""
        FakeOrganization.rows = [_wechat_org()]
        calls = _install_member_sync(monkeypatch)

        response = _build_client().post(
            "/api/v1/wechat-work/callback?UserID=lisi&org_id=1",
            content=b"",
        )

        assert response.status_code == 200
        assert calls[0][0].id == 1
        assert calls[0][1] == "lisi"

    def test_path_org_id_overrides_body_org_id(self, monkeypatch):
        """路径 org_id 优先于正文 org_id。"""
        FakeOrganization.rows = [
            _wechat_org(org_id=1, corp_id="ww-1"),
            _wechat_org(org_id=2, corp_id="ww-2"),
        ]
        calls = _install_member_sync(monkeypatch)

        response = _build_client().post(
            "/api/v1/wechat-work/callback/2",
            json={"org_id": 1, "userid": "wangwu"},
        )

        assert response.status_code == 200
        assert calls[0][0].id == 2
        assert calls[0][1] == "wangwu"

    def test_body_corp_id_wins_over_query_corp_id(self, monkeypatch):
        """正文里的企业 ID 优先于 query。"""
        FakeOrganization.rows = [
            _wechat_org(org_id=1, corp_id="ww-body"),
            _wechat_org(org_id=2, corp_id="ww-query"),
        ]
        calls = _install_member_sync(monkeypatch)

        response = _build_client().post(
            "/api/v1/wechat-work/callback?corp_id=ww-query",
            json={"userid": "lisi", "ToUserName": "ww-body"},
        )

        assert response.status_code == 200
        assert calls[0][0].id == 1

    def test_rejects_when_no_wechat_org_is_bound(self, monkeypatch):
        """没有任何已绑定企微的组织时，拒绝同步。"""
        FakeOrganization.rows = []
        _install_member_sync(monkeypatch)

        response = _build_client().post(
            "/api/v1/wechat-work/callback",
            json={"userid": "lisi"},
        )

        assert response.status_code == 400
        assert "未找到已绑定企业微信的组织" in response.json()["message"]

    def test_rejects_when_multiple_orgs_and_no_identifier(self, monkeypatch):
        """多个企微组织且请求没有 org_id、corp_id 时，拒绝猜测。"""
        FakeOrganization.rows = [
            _wechat_org(org_id=1, corp_id="ww-1"),
            _wechat_org(org_id=2, corp_id="ww-2"),
        ]
        _install_member_sync(monkeypatch)

        response = _build_client().post(
            "/api/v1/wechat-work/callback",
            json={"userid": "lisi"},
        )

        assert response.status_code == 400
        assert "多个" in response.json()["message"]

    def test_rejects_unknown_corp_id(self, monkeypatch):
        """corp_id 对不上任何组织时返回明确错误。"""
        FakeOrganization.rows = [_wechat_org(corp_id="ww-known")]
        _install_member_sync(monkeypatch)

        response = _build_client().post(
            "/api/v1/wechat-work/callback",
            json={"userid": "lisi", "corp_id": "ww-missing"},
        )

        assert response.status_code == 400
        assert "ww-missing" in response.json()["message"]

    def test_missing_userid_is_bad_request_and_raw_body_is_logged(self, monkeypatch, caplog):
        """没有 userid 时拒绝请求，但原文仍写入日志。"""
        caplog.set_level(logging.INFO, logger="app.api.v1.wechat_work")
        raw = '{"event":"not-a-member"}'

        response = _build_client().post(
            "/api/v1/wechat-work/callback",
            content=raw.encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        assert "userid" in response.json()["message"]
        assert raw in caplog.text
        assert "parsed_data=" in caplog.text

    def test_invalid_json_is_bad_request_and_raw_body_is_logged(self, caplog):
        """正文不是合法 JSON 时返回解析错误，并保留原文日志。"""
        caplog.set_level(logging.INFO, logger="app.api.v1.wechat_work")
        raw = "{not-json"

        response = _build_client().post(
            "/api/v1/wechat-work/callback",
            content=raw.encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        assert "JSON" in response.json()["message"]
        assert raw in caplog.text
