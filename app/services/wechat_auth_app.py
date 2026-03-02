"""企微登录 - 应用服务层

跨域服务：衔接企业微信（外部系统）、组织架构域（Employee）和认证域（User/JWT），
处理企微扫码登录、静默授权的完整业务流程。
"""

from typing import Optional
from urllib.parse import quote

from yweb.log import get_logger

logger = get_logger()


class WechatAuthAppService:
    """企业微信登录服务

    职责：
    - 获取企微扫码登录配置
    - 通过企微授权码换取本系统 JWT Token
    - 获取企微内部静默授权 URL
    """

    def __init__(self, org_models, auth_service, login_response_builder=None):
        """
        Args:
            org_models: OrgModels 实例（setup_organization 的返回值）
            auth_service: 认证服务实例（用于签发 JWT Token）
            login_response_builder: 登录响应构建函数（保持与标准登录一致的格式）
        """
        self.org_models = org_models
        self.auth_service = auth_service
        self.login_response_builder = login_response_builder

    # ==================== 公开方法 ====================

    def get_login_config(self, base_url: str) -> dict:
        """获取企微扫码登录参数

        Args:
            base_url: 应用基础 URL（如 http://localhost:8001）

        Returns:
            {"enabled": True/False, "corp_id": ..., "agent_id": ..., ...}
        """
        try:
            org, wechat_config = self._get_wechat_login_org()
            redirect_uri = f"{base_url.rstrip('/')}/api/v1/auth/wechat-work/callback"
            return {
                "enabled": True,
                "corp_id": org.external_corp_id,
                "agent_id": wechat_config["login_agent_id"],
                "redirect_uri": redirect_uri,
                "state": "",  # 前端自行生成随机 state 用于 CSRF 防护
            }
        except ValueError:
            return {"enabled": False}

    def login_by_code(
        self, code: str, ip_address: str = "unknown", user_agent: str = "",
    ) -> dict:
        """通过企微授权码登录，返回 JWT Token

        Args:
            code: 企微授权码（auth_code 或 oauth code）
            ip_address: 客户端 IP
            user_agent: 客户端 User-Agent

        Returns:
            登录响应字典（包含 access_token, refresh_token, user 等）

        Raises:
            ValueError: 授权码无效 / 用户未找到 / 账号被禁用等
        """
        org, wechat_config = self._get_wechat_login_org()

        # 1. 用 code 换取企微 userid
        wechat_userid = self._exchange_code_for_userid(
            org.external_corp_id, wechat_config["login_secret"], code,
        )

        # 2. 通过 userid 查找本地用户
        user = self._find_user_by_wechat_userid(wechat_userid, org)

        # 3. 签发 JWT Token
        access_token = self.auth_service.create_access_token(user)
        refresh_token = self.auth_service.create_refresh_token(user)

        # 4. 记录登录
        self.auth_service.on_authenticate_success(
            user, ip_address=ip_address, user_agent=user_agent,
        )
        self.auth_service.update_last_login(
            user.id, ip_address=ip_address, user_agent=user_agent,
            status="success",
        )

        # 5. 构建响应
        if self.login_response_builder:
            return self.login_response_builder(user, access_token, refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
            },
        }

    def get_oauth_url(self, redirect_uri: str, state: str = "") -> dict:
        """获取企微内部静默授权 URL

        Args:
            redirect_uri: 授权成功后的前端回调地址
            state: 状态参数（CSRF 防护）

        Returns:
            {"oauth_url": "https://open.weixin.qq.com/..."}

        Raises:
            ValueError: 未配置企微登录
        """
        org, wechat_config = self._get_wechat_login_org()

        oauth_url = (
            f"https://open.weixin.qq.com/connect/oauth2/authorize"
            f"?appid={org.external_corp_id}"
            f"&redirect_uri={quote(redirect_uri)}"
            f"&response_type=code"
            f"&scope=snsapi_base"
            f"&state={state}"
            f"&agentid={wechat_config['login_agent_id']}"
            f"#wechat_redirect"
        )
        return {"oauth_url": oauth_url}

    # ==================== 内部方法 ====================

    def _get_wechat_login_org(self):
        """获取已配置企微登录的组织（返回第一个匹配的）

        Returns:
            (Organization, wechat_config_dict) 元组

        Raises:
            ValueError: 未找到配置了企微扫码登录的组织
        """
        from yweb.organization import ExternalSource

        if not self.org_models:
            raise ValueError("未配置组织架构模块")

        Organization = self.org_models.Organization
        orgs = Organization.query.filter(
            Organization.external_source == ExternalSource.WECHAT_WORK.value,
        ).all()

        for org in orgs:
            config = org.get_external_config_dict()
            wechat_config = config.get("wechat_work", {})
            if wechat_config.get("login_agent_id") and wechat_config.get("login_secret"):
                return org, wechat_config

        raise ValueError("未找到配置了企微扫码登录的组织（需配置 login_agent_id 和 login_secret）")

    def _get_wechat_login_org_by_corp_id(self, corp_id: str):
        """根据 corp_id 获取已配置企微登录的组织

        Args:
            corp_id: 企业微信 corp_id

        Returns:
            (Organization, wechat_config_dict) 元组

        Raises:
            ValueError: 未找到配置了企微扫码登录的组织
        """
        from yweb.organization import ExternalSource

        if not self.org_models:
            raise ValueError("未配置组织架构模块")

        Organization = self.org_models.Organization
        org = Organization.query.filter(
            Organization.external_source == ExternalSource.WECHAT_WORK.value,
            Organization.external_corp_id == corp_id,
        ).first()

        if not org:
            raise ValueError(f"未找到配置了企微扫码登录的组织（corp_id: {corp_id}）")

        config = org.get_external_config_dict()
        wechat_config = config.get("wechat_work", {})
        if not (wechat_config.get("login_agent_id") and wechat_config.get("login_secret")):
            raise ValueError(f"组织 {org.name} 未配置企微登录参数（需配置 login_agent_id 和 login_secret）")

        return org, wechat_config

    def _exchange_code_for_userid(
        self, corp_id: str, login_secret: str, code: str,
    ) -> str:
        """用企微授权码换取 userid

        Returns:
            企微 userid

        Raises:
            ValueError: 授权码无效或已过期
        """
        from wechatpy.enterprise import WeChatClient

        client = WeChatClient(corp_id, login_secret)
        try:
            user_info = client.oauth.get_user_info(code)
        except Exception as e:
            logger.error(f"企微授权码换取用户身份失败: {e}")
            raise ValueError("授权码无效或已过期，请重新扫码")

        wechat_userid = user_info.get("userid") or user_info.get("UserId")
        if not wechat_userid:
            raise ValueError("未获取到企微用户身份，请确认授权码有效")

        logger.info(f"企微登录: userid={wechat_userid}")
        return wechat_userid

    def _find_user_by_wechat_userid(self, wechat_userid: str, org):
        """通过企微 userid 查找本地 User

        Returns:
            User 实体

        Raises:
            ValueError: 用户未找到 / 未开通账号 / 账号被禁用
        """
        EmployeeOrgRel = self.org_models.EmployeeOrgRel
        Employee = self.org_models.Employee

        # 1. 通过 EmployeeOrgRel 找 employee_id
        rel = EmployeeOrgRel.query.filter(
            EmployeeOrgRel.org_id == org.id,
            EmployeeOrgRel.external_user_id == wechat_userid,
        ).first()

        if not rel:
            raise ValueError("未找到该企业微信用户，请先同步通讯录")

        # 2. 查找 Employee
        employee = Employee.get(rel.employee_id)
        if not employee:
            raise ValueError("员工记录异常，请联系管理员")

        # 3. Employee → User（通过 user_id 关系）
        user_id = getattr(employee, 'user_id', None)
        if not user_id:
            raise ValueError(
                f"员工 [{employee.name}] 尚未开通系统账号，请联系管理员"
            )

        from app.models_registry import User
        user = User.get(user_id)
        if not user:
            raise ValueError("关联的用户账号不存在，请联系管理员")

        if not user.is_active:
            raise ValueError("用户账号已被禁用")

        return user
