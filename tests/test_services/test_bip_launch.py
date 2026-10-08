"""BIP 单点登录跳转"""

from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest

from app.services.bip_launch import (
    BipLaunchService,
    build_login_url,
    generate_security,
    request_access_token,
)


class _AppQuery:
    """按过滤条件返回固定应用"""

    def __init__(self, application):
        self.application = application
        self.filters = {}

    def filter_by(self, **kwargs):
        self.filters = kwargs
        return self

    def first(self):
        app = self.application
        if app is None:
            return None
        if self.filters.get("code") != getattr(app, "code", None):
            return None
        if self.filters.get("is_active") and not app.is_active:
            return None
        return app


class _AppModel:
    def __init__(self, application):
        self.query = _AppQuery(application)


class BipApplication:
    """带重定向地址的 bip 应用"""

    def __init__(self, redirect_uris, is_active=True):
        self.code = "bip"
        self.is_active = is_active
        self._redirect_uris = redirect_uris

    def get_redirect_uris(self):
        return list(self._redirect_uris)


def _config():
    return {
        "base_url": "http://193.111.99.222:9090",
        "client_id": "001",
        "client_secret": "123456",
        "dsname": "NCBIP",
        "busi_center_code": "001",
        "lang_code": "simpchn",
        "auth_type": "default",
        "redirect_uri": "http://193.111.99.222:9090/nccloud",
    }


class TestBipLaunch:
    """BIP 登录地址生成"""

    def test_security_matches_known_vector(self):
        """固定时间戳下，签名等于已核对的 Base64 结果"""
        security = generate_security("zhb", "123456", now_ms=1790731234567)
        assert security == "iFT+8xZbD1Cw0sqUsfM8DQc9sFCgHaVVQOhyrAeAxq8="

    def test_login_url_uses_token_and_homepage(self):
        """登录地址带一次性 token，并在成功后进入 BIP 首页"""
        url = build_login_url(
            "http://193.111.99.222:9090",
            "abc12345token",
            "http://193.111.99.222:9090/nccloud",
        )
        assert url == (
            "http://193.111.99.222:9090/nccloud/resources/uap/rbac/thirdpartylogin/main/index.html"
            "?accesstoken=abc12345token"
            "&redirect_uri=http://193.111.99.222:9090/nccloud"
        )

    def test_request_encodes_plus_in_security(self, monkeypatch):
        """签名里的加号按表单规则转成 %2B 再提交"""
        captured = {}

        def fake_post(url, content, headers, timeout):
            captured["url"] = url
            captured["body"] = content.decode("utf-8")
            response = Mock()
            response.status_code = 200
            response.text = "68541eb35c8bc6ed05694c042a78a183"
            return response

        monkeypatch.setattr("app.services.bip_launch.httpx.post", fake_post)
        monkeypatch.setattr(
            "app.services.bip_launch.generate_security",
            lambda usercode, client_security: "abc+def=",
        )

        token = request_access_token("zhangsan", _config())

        assert token == "68541eb35c8bc6ed05694c042a78a183"
        assert captured["url"].endswith("/service/genThirdPartyAccessToken")
        assert "usercode=zhangsan" in captured["body"]
        assert "security=abc%2Bdef=" in captured["body"]
        assert "security=abc+def=" not in captured["body"]

    def test_bip_rejection_does_not_return_token(self, monkeypatch):
        """BIP 返回 401 时不产生登录令牌"""
        response = Mock(status_code=401, text="")
        monkeypatch.setattr("app.services.bip_launch.httpx.post", lambda *args, **kwargs: response)

        with pytest.raises(ValueError, match="拒绝签发"):
            request_access_token("zhangsan", _config())

    def test_empty_success_body_is_rejected(self, monkeypatch):
        """BIP 返回 200 但正文为空时不产生登录令牌"""
        response = Mock(status_code=200, text="   ")
        monkeypatch.setattr("app.services.bip_launch.httpx.post", lambda *args, **kwargs: response)

        with pytest.raises(ValueError, match="未返回有效登录令牌"):
            request_access_token("zhangsan", _config())

    def test_launch_returns_url_for_active_bip_app(self, monkeypatch):
        """启用的 bip 应用用当前用户登录名换到登录地址"""
        monkeypatch.setattr(
            "app.services.bip_launch._require_config",
            lambda: _config(),
        )
        monkeypatch.setattr(
            "app.services.bip_launch.request_access_token",
            lambda usercode, config: f"token-for-{usercode}",
        )
        application = BipApplication(["http://193.111.99.222:9090/nccloud"])
        service = BipLaunchService(_AppModel(application))

        url = service.launch(SimpleNamespace(username=" zhangsan "))

        assert "accesstoken=token-for-zhangsan" in url
        assert url.endswith("&redirect_uri=http://193.111.99.222:9090/nccloud")

    def test_launch_takes_host_and_landing_page_from_first_redirect_uri(self, monkeypatch):
        """登录主机和登录后页面来自应用的第一条重定向 URI，配置中的地址不生效"""
        monkeypatch.setattr("app.services.bip_launch._require_config", lambda: _config())
        captured = {}

        def fake_token(usercode, config):
            captured["base_url"] = config["base_url"]
            captured["redirect_uri"] = config["redirect_uri"]
            return "token-from-bip"

        monkeypatch.setattr("app.services.bip_launch.request_access_token", fake_token)
        application = BipApplication([
            "  http://10.1.2.3:9090/nccloud  ",
            "http://ignored.example/other",
        ])
        service = BipLaunchService(_AppModel(application))

        url = service.launch(SimpleNamespace(username="zhangsan"))

        assert captured["base_url"] == "http://10.1.2.3:9090"
        assert captured["redirect_uri"] == "http://10.1.2.3:9090/nccloud"
        assert url.startswith(
            "http://10.1.2.3:9090/nccloud/resources/uap/rbac/thirdpartylogin/main/index.html?"
        )
        assert "accesstoken=token-from-bip" in url
        assert url.endswith("&redirect_uri=http://10.1.2.3:9090/nccloud")
        assert "193.111.99.222" not in url
        assert "ignored.example" not in url

    def test_launch_rejects_application_without_redirect_uri(self, monkeypatch):
        """应用没有重定向地址时，不向 BIP 申请令牌"""
        monkeypatch.setattr("app.services.bip_launch._require_config", lambda: _config())
        monkeypatch.setattr(
            "app.services.bip_launch.request_access_token",
            lambda usercode, config: "should-not-run",
        )
        service = BipLaunchService(_AppModel(BipApplication([])))

        with pytest.raises(ValueError, match="没有重定向地址"):
            service.launch(SimpleNamespace(username="zhangsan"))

    def test_launch_rejects_redirect_uri_without_host(self, monkeypatch):
        """重定向地址缺少协议或主机时，不向 BIP 申请令牌"""
        monkeypatch.setattr("app.services.bip_launch._require_config", lambda: _config())
        monkeypatch.setattr(
            "app.services.bip_launch.request_access_token",
            lambda usercode, config: "should-not-run",
        )
        service = BipLaunchService(_AppModel(BipApplication(["/nccloud"])))

        with pytest.raises(ValueError, match="缺少协议或主机"):
            service.launch(SimpleNamespace(username="zhangsan"))

    def test_launch_rejects_inactive_app(self):
        """停用的 bip 应用不能发起登录"""
        application = SimpleNamespace(code="bip", is_active=False)
        service = BipLaunchService(_AppModel(application))

        with pytest.raises(ValueError, match="不存在或已停用"):
            service.launch(SimpleNamespace(username="zhangsan"))

    def test_launch_rejects_user_without_username(self):
        """没有登录名的用户不能对应到 BIP 用户"""
        application = SimpleNamespace(code="bip", is_active=True)
        service = BipLaunchService(_AppModel(application))

        with pytest.raises(ValueError, match="没有登录名"):
            service.launch(SimpleNamespace(username="  "))

    def test_connection_failure_is_reported(self, monkeypatch):
        """BIP 连不上时给出连接失败，而不是返回地址"""
        def fake_post(*args, **kwargs):
            raise httpx.ConnectError("refused")

        monkeypatch.setattr("app.services.bip_launch.httpx.post", fake_post)

        with pytest.raises(ValueError, match="无法连接 BIP"):
            request_access_token("zhangsan", _config())
