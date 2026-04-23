"""ApplicationService 测试"""

import pytest

from app.domain.application.entities import Application
from app.domain.application.services import ApplicationService
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
