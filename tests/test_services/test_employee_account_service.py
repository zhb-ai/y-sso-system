"""员工账号服务测试"""

from types import SimpleNamespace

import pytest

from app.services.employee_app import USERNAME_MAX_LEN, EmployeeAccountService


class TestEmployeeAccountService:
    """创建员工账号时的用户名规则"""

    @pytest.fixture
    def service(self):
        return EmployeeAccountService(employee_model=object)

    def test_resolve_username_uses_enterprise_wechat_user_id(self, service):
        """有企微 userid 时应直接作为登录名，不用姓名拼音"""
        employee = SimpleNamespace(
            id=1,
            name="张三",
            enterprise_wechat_user_id="WeiXinZhang001",
        )
        assert service._resolve_username(employee) == "WeiXinZhang001"

    def test_resolve_username_strips_wechat_user_id(self, service):
        """企微 userid 应去掉首尾空白"""
        employee = SimpleNamespace(
            id=1,
            name="张三",
            enterprise_wechat_user_id="  WeiXinZhang001  ",
        )
        assert service._resolve_username(employee) == "WeiXinZhang001"

    def test_resolve_username_raises_when_wechat_user_id_missing(self, service):
        """没有企微 userid 时应拒绝创建，不能回退拼音"""
        employee = SimpleNamespace(
            id=1,
            name="张三",
            enterprise_wechat_user_id=None,
        )
        with pytest.raises(ValueError, match="企业微信 userid"):
            service._resolve_username(employee)

    def test_resolve_username_raises_when_wechat_user_id_blank(self, service):
        """空白企微 userid 应视为缺失"""
        employee = SimpleNamespace(
            id=1,
            name="张三",
            enterprise_wechat_user_id="   ",
        )
        with pytest.raises(ValueError, match="企业微信 userid"):
            service._resolve_username(employee)

    def test_resolve_username_raises_when_wechat_user_id_too_long(self, service):
        """超过用户名列长度时应拒绝"""
        employee = SimpleNamespace(
            id=1,
            name="张三",
            enterprise_wechat_user_id="W" * (USERNAME_MAX_LEN + 1),
        )
        with pytest.raises(ValueError, match="超过"):
            service._resolve_username(employee)

    def test_create_account_raises_when_employee_has_no_wechat_id(self):
        """创建账号在缺少企微 userid 时应在写用户前失败"""
        employee = SimpleNamespace(
            id=21,
            name="张三",
            user_id=None,
            enterprise_wechat_user_id=None,
            employee_org_rels=[],
        )
        service = EmployeeAccountService(
            employee_model=SimpleNamespace(get=lambda _id: employee),
        )
        with pytest.raises(ValueError, match="企业微信 userid"):
            service.create_account_for_employee(21)
