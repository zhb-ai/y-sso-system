"""ApplicationService 测试"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.domain.application.entities import Application, BipLaunchRecord
from app.domain.application.services import ApplicationService
from app.services.bip_launch import BipLaunchService
from yweb.orm import BaseModel, init_database


class RoleModel(BaseModel):
    """最小角色模型，供测试建表使用"""
    __tablename__ = "role"
    __table_args__ = {"extend_existing": True}


@pytest.fixture(scope="function")
def application_service():
    """为每个测试提供独立的应用服务和内存数据库"""
    engine, _ = init_database("sqlite:///:memory:")
    BaseModel.metadata.create_all(bind=engine)

    yield ApplicationService()

    BaseModel.metadata.drop_all(bind=engine)
    engine.dispose()


class TestApplicationService:
    """ApplicationService 行为测试"""

    def test_attach_call_counts_sets_24h_and_7d_counts(self, application_service, monkeypatch):
        """应用列表统计应补充 24 小时和 7 天调用次数"""
        apps = [
            type("AppStub", (), {"id": 1})(),
            type("AppStub", (), {"id": 2})(),
        ]
        page_result = type("PageStub", (), {"rows": apps})()

        def _get_authorization_counts_since(app_ids, since):
            assert app_ids == [1, 2]
            return {1: 3, 2: 5} if since.day == 7 else {1: 10}

        monkeypatch.setattr(
            application_service,
            "_get_authorization_counts_since",
            _get_authorization_counts_since,
        )

        application_service._attach_call_counts_to_page(
            page_result,
            now=datetime(2026, 1, 8, tzinfo=timezone.utc),
        )

        assert apps[0].call_count_24h == 3
        assert apps[0].call_count_7d == 10
        assert apps[1].call_count_24h == 5
        assert apps[1].call_count_7d == 0

    def test_bip_launch_counts_follow_24h_and_7d_windows(self, application_service):
        """BIP 成功登录计入 24 小时和 7 天，窗口外和其他应用不计入"""
        bip = application_service.create_application(
            name="BIP",
            code="bip",
            redirect_uris=["http://10.0.0.8/nccloud"],
        )
        other = application_service.create_application(
            name="Other",
            code="other_app",
            redirect_uris=["http://localhost/callback"],
        )
        now = datetime(2026, 10, 22, 8, 0, tzinfo=timezone.utc)
        BipLaunchRecord.record(bip.id, now - timedelta(hours=1))
        BipLaunchRecord.record(bip.id, now - timedelta(days=2))
        BipLaunchRecord.record(bip.id, now - timedelta(days=8))
        BipLaunchRecord.record(other.id, now - timedelta(hours=1))

        page = type("PageStub", (), {"rows": [bip, other]})()
        application_service._attach_call_counts_to_page(page, now=now)

        assert bip.call_count_24h == 1
        assert bip.call_count_7d == 2
        assert other.call_count_24h == 1
        assert other.call_count_7d == 1

    def test_successful_bip_launch_is_counted(self, application_service, monkeypatch):
        """启用的 bip 应用成功换到令牌后，列表中的调用次数加一"""
        bip = application_service.create_application(
            name="BIP",
            code="bip",
            redirect_uris=["http://10.0.0.8/nccloud"],
        )
        monkeypatch.setattr("app.services.bip_launch._require_config", lambda: {})
        monkeypatch.setattr(
            "app.services.bip_launch.request_access_token",
            lambda usercode, config: "token-for-test",
        )

        url = BipLaunchService(Application).launch(SimpleNamespace(username="zhangsan"))

        assert "accesstoken=token-for-test" in url
        page = application_service.list_applications()
        listed = next(row for row in page.rows if row.id == bip.id)
        assert listed.call_count_24h == 1
        assert listed.call_count_7d == 1

    def test_rejected_bip_launch_is_not_counted(self, application_service, monkeypatch):
        """BIP 拒绝签发令牌时不增加调用次数"""
        bip = application_service.create_application(
            name="BIP",
            code="bip",
            redirect_uris=["http://10.0.0.8/nccloud"],
        )

        def _reject(usercode, config):
            raise ValueError("BIP 拒绝签发登录令牌")

        monkeypatch.setattr("app.services.bip_launch._require_config", lambda: {})
        monkeypatch.setattr("app.services.bip_launch.request_access_token", _reject)

        with pytest.raises(ValueError, match="拒绝签发"):
            BipLaunchService(Application).launch(SimpleNamespace(username="zhangsan"))

        page = application_service.list_applications()
        listed = next(row for row in page.rows if row.id == bip.id)
        assert listed.call_count_24h == 0
        assert listed.call_count_7d == 0

    def test_create_public_application_clears_secret(self, application_service):
        """创建公开客户端时不应保留客户端密钥"""
        app = application_service.create_application(
            name="Public App",
            code="public_app",
            description="公开客户端",
            redirect_uris=["http://localhost/callback"],
            client_type="public",
        )

        assert app.client_type == "public"
        assert app.client_secret == ""

    def test_update_application_to_public_clears_secret(self, application_service):
        """应用切换为公开客户端时应清空客户端密钥"""
        app = application_service.create_application(
            name="Confidential App",
            code="confidential_app",
            redirect_uris=["http://localhost/callback"],
            client_type="confidential",
        )

        assert app.client_secret

        updated = application_service.update_application(app.id, client_type="public")

        assert updated.client_type == "public"
        assert updated.client_secret == ""

    def test_update_application_to_confidential_generates_secret_when_missing(self, application_service):
        """公开客户端切回机密客户端时应自动生成客户端密钥"""
        app = application_service.create_application(
            name="Public App",
            code="public_to_confidential",
            redirect_uris=["http://localhost/callback"],
            client_type="public",
        )

        assert app.client_secret == ""

        updated = application_service.update_application(app.id, client_type="confidential")

        assert updated.client_type == "confidential"
        assert updated.client_secret
        assert Application.get(app.id).client_secret == updated.client_secret

    def test_create_application_persists_allowed_ip_cidrs(self, application_service):
        """创建应用时应保存 IP 白名单"""
        app = application_service.create_application(
            name="Whitelist App",
            code="whitelist_app",
            redirect_uris=["http://localhost/callback"],
            allowed_ip_cidrs=["203.0.113.10", "198.51.100.0/24"],
        )

        assert app.get_allowed_ip_cidrs() == ["203.0.113.10", "198.51.100.0/24"]
        assert Application.get(app.id).get_allowed_ip_cidrs() == ["203.0.113.10", "198.51.100.0/24"]

    def test_update_application_persists_allowed_ip_cidrs(self, application_service):
        """更新应用时应覆盖保存 IP 白名单"""
        app = application_service.create_application(
            name="Whitelist App",
            code="update_whitelist_app",
            redirect_uris=["http://localhost/callback"],
        )

        updated = application_service.update_application(
            app.id,
            allowed_ip_cidrs=["203.0.113.10/32", "198.51.100.0/24"],
        )

        assert updated.get_allowed_ip_cidrs() == ["203.0.113.10/32", "198.51.100.0/24"]
        assert Application.get(app.id).get_allowed_ip_cidrs() == ["203.0.113.10/32", "198.51.100.0/24"]

    def test_validate_source_ip_accepts_ip_in_whitelist(self, application_service):
        """来源 IP 命中白名单时应允许访问"""
        app = application_service.create_application(
            name="Allowed App",
            code="allowed_app",
            redirect_uris=["http://localhost/callback"],
            allowed_ip_cidrs=["203.0.113.0/24"],
        )

        app.validate_source_ip("203.0.113.10")

    def test_validate_source_ip_rejects_ip_outside_whitelist(self, application_service):
        """来源 IP 不在白名单时应拒绝访问"""
        app = application_service.create_application(
            name="Denied App",
            code="denied_app",
            redirect_uris=["http://localhost/callback"],
            allowed_ip_cidrs=["203.0.113.0/24"],
        )

        with pytest.raises(ValueError, match="白名单"):
            app.validate_source_ip("198.51.100.10")
