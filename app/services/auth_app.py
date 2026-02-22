"""认证应用服务

标准认证流程（登录/登出/刷新令牌/踢出用户）已由 yweb 框架
通过 create_auth_router() 提供，不再需要应用层协调。

此文件保留框架未覆盖的项目特有业务逻辑：
- 用户注册
- 用户自助修改密码
- 管理员强制重置密码

注意：Service 层只返回实体对象或简单数据，DTO 转换由 API 层负责。
"""

from app.domain.auth.model.user import User
from yweb.log import get_logger
from yweb.auth import PasswordHelper, UsernameValidator, PasswordValidator

logger = get_logger()


class AuthApplicationService:
    """认证应用服务

    标准认证端点已由框架提供，此服务处理项目特有逻辑：
    - 用户注册
    - 自助修改密码
    - 强制重置密码
    """

    def register(
        self,
        username: str,
        password: str,
        email: str = None,
        phone: str = None,
    ) -> User:
        """用户注册

        Args:
            username: 用户名
            password: 密码（明文）
            email: 邮箱
            phone: 手机号

        Returns:
            注册成功返回用户实体

        Raises:
            ValueError: 用户名/密码格式无效
        """
        logger.info(f"用户尝试注册: {username}")

        UsernameValidator.validate_or_raise(username)
        PasswordValidator.validate_or_raise(password)

        user = User(
            username=username,
            password_hash=PasswordHelper.hash(password),
            email=email,
            phone=phone,
            is_active=True,
        )
        user.add(True)

        logger.info(f"用户注册成功: {username} (ID: {user.id})")
        return user

    def change_password(self, user, old_password: str, new_password: str):
        """用户自助修改密码

        验证旧密码后设置新密码，同时清除「首次登录强制修改」标记。

        Args:
            user: 当前用户实体（已通过认证）
            old_password: 当前密码
            new_password: 新密码

        Raises:
            ValueError: 当前密码错误 / 新密码强度不足
        """
        if not PasswordHelper.verify(old_password, user.password_hash):
            raise ValueError("当前密码错误")

        PasswordValidator.validate_or_raise(new_password)

        user.password_hash = PasswordHelper.hash(new_password)
        if hasattr(user, 'must_change_password'):
            user.must_change_password = False
        user.save(commit=True)

        logger.info(f"用户 {user.username}(ID={user.id}) 修改密码成功")

    def force_reset_password(self, user_id: int, temp_password: str = "000000") -> str:
        """强制重置用户密码为临时密码

        重置后用户首次登录时需强制修改密码。

        Args:
            user_id: 用户 ID
            temp_password: 临时密码，默认 "000000"

        Returns:
            临时密码字符串

        Raises:
            ValueError: 用户不存在
        """
        user = User.get(user_id)
        if not user:
            raise ValueError(f"用户不存在: ID={user_id}")

        user.password_hash = PasswordHelper.hash(temp_password, validate=False)
        if hasattr(user, 'must_change_password'):
            user.must_change_password = True
        user.save(commit=True)

        logger.info(f"用户 {user.username}(ID={user.id}) 密码已强制重置")
        return temp_password
