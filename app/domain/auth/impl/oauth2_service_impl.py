"""OAuth2 服务实现

使用 Active Record 模式，委托给 application 域的服务层处理。
保留此类作为 auth 域到 application 域的桥梁。

注意：核心 OAuth2 令牌管理逻辑已移至 app.domain.application.services.OAuth2TokenService，
此处仅作为便捷入口。
"""

from typing import Optional, List

from yweb.log import get_logger
from app.domain.application.services import ApplicationService, OAuth2TokenService
from app.domain.application.entities import OAuth2Token

logger = get_logger()


class OAuth2ServiceImpl:
    """OAuth2 服务实现

    委托给 application 域的 OAuth2TokenService 处理。

    用法：
        oauth2_service = OAuth2ServiceImpl()
        token = oauth2_service.create_token(application_id=1, user_id=1)
        valid_token = oauth2_service.validate_token(access_token="...")
    """

    def __init__(self):
        self.app_service = ApplicationService()
        self.token_service = OAuth2TokenService(self.app_service)

    def create_token(
        self, application_id: int, user_id: int, expires_minutes: int = 30
    ) -> OAuth2Token:
        """创建 OAuth2 令牌

        Raises:
            ValueError: 创建失败
        """
        return self.token_service.create_token(
            application_id, user_id, expires_minutes
        )

    def validate_token(self, access_token: str) -> OAuth2Token:
        """验证访问令牌

        Raises:
            ValueError: 令牌无效 / 已过期
        """
        return self.token_service.validate_access_token(access_token)

    def refresh_token(
        self, client_id: str, client_secret: str, refresh_token: str
    ) -> OAuth2Token:
        """刷新访问令牌

        Raises:
            ValueError: 凭证无效 / 刷新令牌无效
        """
        return self.token_service.refresh_token(
            client_id, client_secret, refresh_token
        )

    def revoke_token(self, access_token: str) -> None:
        """撤销令牌"""
        self.token_service.revoke_token(access_token)

    def revoke_user_tokens(
        self, user_id: int, application_id: Optional[int] = None
    ) -> None:
        """撤销用户的令牌"""
        self.token_service.revoke_user_tokens(user_id, application_id)

    def get_user_tokens(self, user_id: int) -> List[OAuth2Token]:
        """获取用户的所有令牌"""
        return self.token_service.get_user_tokens(user_id)
