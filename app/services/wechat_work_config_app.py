"""企微配置 - 应用服务层

处理企业微信组织绑定/解绑/配置查询等跨聚合操作。
涉及 Organization（组织架构域）和 WechatWorkClient（企微域）。
"""

from yweb.log import get_logger

logger = get_logger()


class WechatWorkConfigAppService:
    """企微配置管理服务

    职责：
    - 绑定企微配置（含连接验证）
    - 解绑企微配置
    - 查看绑定配置（Secret 脱敏）
    """

    def __init__(self, org_models):
        """
        Args:
            org_models: OrgModels 实例（setup_organization 的返回值）
        """
        self.org_models = org_models
        self.Organization = org_models.Organization

    def bind(
        self,
        org_id: int,
        corp_id: str,
        corp_secret: str,
        callback_token: str = None,
        callback_aes_key: str = None,
        login_agent_id: str = None,
        login_secret: str = None,
    ) -> dict:
        """绑定企业微信配置

        Args:
            org_id: 组织 ID
            corp_id: 企业微信企业 ID
            corp_secret: 通讯录同步 Secret
            callback_token: 回调 Token（可选）
            callback_aes_key: 回调 EncodingAESKey（可选）
            login_agent_id: 自建应用 AgentID（可选，用于扫码登录）
            login_secret: 自建应用 Secret（可选，用于扫码登录）

        Returns:
            {"org_id": ..., "corp_id": ...}

        Raises:
            ValueError: 组织不存在 / 已绑定其他系统 / 连接验证失败
        """
        from yweb.organization import ExternalSource

        org = self.Organization.get(org_id)
        if not org:
            raise ValueError(f"组织不存在: id={org_id}")

        # 如果已绑定其他外部系统，不允许覆盖
        if (
            org.external_source
            and org.external_source != ExternalSource.NONE.value
            and org.external_source != ExternalSource.WECHAT_WORK.value
        ):
            raise ValueError(
                f"组织 [{org.name}] 已绑定其他外部系统: {org.external_source}"
            )

        # 验证连接（尝试获取 access_token）
        from app.domain.wechat_work.client import WechatWorkClient

        test_client = WechatWorkClient(corp_id=corp_id, corp_secret=corp_secret)
        try:
            test_client.client.fetch_access_token()
        except Exception as e:
            raise ValueError(
                f"企业微信连接验证失败，请检查 corp_id 和 Secret 是否正确: {e}"
            )

        # 保存配置
        org.external_source = ExternalSource.WECHAT_WORK.value
        org.external_corp_id = corp_id

        wechat_config = {"corp_secret": corp_secret}
        if callback_token:
            wechat_config["callback_token"] = callback_token
        if callback_aes_key:
            wechat_config["callback_aes_key"] = callback_aes_key
        if login_agent_id:
            wechat_config["login_agent_id"] = login_agent_id
        if login_secret:
            wechat_config["login_secret"] = login_secret

        org.set_external_config_dict({"wechat_work": wechat_config})
        org.save(commit=True)

        logger.info(f"企业微信绑定成功: org_id={org.id}, corp_id={corp_id}")
        return {"org_id": org.id, "corp_id": corp_id}

    def unbind(self, org_id: int) -> dict:
        """解绑企业微信配置

        清除组织的企微绑定配置，不会删除已同步的部门和员工数据。

        Args:
            org_id: 组织 ID

        Returns:
            {"org_id": ...}

        Raises:
            ValueError: 组织不存在 / 未绑定企微
        """
        from yweb.organization import ExternalSource

        org = self.Organization.get(org_id)
        if not org:
            raise ValueError(f"组织不存在: id={org_id}")

        if org.external_source != ExternalSource.WECHAT_WORK.value:
            raise ValueError(f"组织 [{org.name}] 未绑定企业微信")

        org.external_source = ExternalSource.NONE.value
        org.external_corp_id = None
        org.external_config = None
        org.save(commit=True)

        logger.info(f"企业微信解绑成功: org_id={org.id}")
        return {"org_id": org.id}

    def get_config(self, org_id: int) -> dict:
        """查看企微绑定配置（Secret 脱敏）

        Args:
            org_id: 组织 ID

        Returns:
            包含绑定状态和脱敏配置信息的字典

        Raises:
            ValueError: 组织不存在
        """
        from yweb.organization import ExternalSource

        org = self.Organization.get(org_id)
        if not org:
            raise ValueError(f"组织不存在: id={org_id}")

        is_bound = org.external_source == ExternalSource.WECHAT_WORK.value
        config = org.get_external_config_dict()
        wechat_config = config.get("wechat_work", {})

        return {
            "org_id": org.id,
            "org_name": org.name,
            "is_bound": is_bound,
            "corp_id": org.external_corp_id or "",
            "corp_secret": self._mask(wechat_config.get("corp_secret", "")) if is_bound else "",
            "has_callback_config": bool(
                wechat_config.get("callback_token")
                and wechat_config.get("callback_aes_key")
            ),
            "callback_token": self._mask(wechat_config.get("callback_token", "")) if is_bound else "",
            "callback_aes_key": self._mask(wechat_config.get("callback_aes_key", "")) if is_bound else "",
            "has_login_config": bool(
                wechat_config.get("login_agent_id")
                and wechat_config.get("login_secret")
            ),
            "login_agent_id": wechat_config.get("login_agent_id", "") if is_bound else "",
            "login_secret": self._mask(wechat_config.get("login_secret", "")) if is_bound else "",
        }

    @staticmethod
    def _mask(value: str) -> str:
        """脱敏显示"""
        if not value or len(value) <= 8:
            return "****"
        return value[:4] + "****" + value[-4:]
