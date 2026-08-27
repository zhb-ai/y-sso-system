"""员工账号 - 应用服务层

跨域服务：衔接组织架构域（Employee）和认证域（User），
处理员工自动创建用户账号的业务逻辑。
"""

from typing import Type

from yweb.auth import PasswordHelper
from yweb.log import get_logger

from app.domain.auth.model.user import User, UserRoleEnum
from app.utils.infrastructure_utils import generate_strong_password

logger = get_logger()

# 员工账号默认密码（首次登录需强制修改）
DEFAULT_PASSWORD = "000000"
# AbstractUser.username 列长 50
USERNAME_MAX_LEN = 50


class EmployeeAccountService:
    """员工账号服务

    为员工自动创建/关联内部用户账号：
    - 用户名使用员工的企业微信 userid（enterprise_wechat_user_id）
    - 默认密码首次登录强制修改
    - 分配「内部员工」角色
    - 关联 employee.user_id
    """

    def __init__(self, employee_model: Type):
        self.employee_model = employee_model

    def create_account_for_employee(
        self,
        employee_id: int,
        username: str = None,
    ) -> dict:
        """为员工创建用户账号

        使用默认密码 000000，首次登录时强制修改。

        Args:
            employee_id: 员工ID
            username: 指定用户名（不传则自动生成）

        Returns:
            包含 user_id, username, employee_id, employee_name 的字典

        Raises:
            ValueError: 员工不存在 / 已有账号 / 用户名冲突
        """
        # 1. 获取员工
        employee = self.employee_model.get(employee_id)
        if not employee:
            raise ValueError(f"员工不存在: ID={employee_id}")

        # 2. 检查是否已有账号
        if getattr(employee, 'user_id', None):
            raise ValueError("该员工已关联用户账号")

        # 3. 检查雇佣状态：离职/停职的员工不允许创建账号
        if hasattr(employee, 'employee_org_rels'):
            rels = employee.employee_org_rels
            if rels and all(rel.status <= 0 for rel in rels):
                # 所有组织中都非活跃
                status_names = {-1: "离职", 0: "停职"}
                first_status = rels[0].status
                status_name = status_names.get(first_status, "非活跃")
                raise ValueError(f"该员工当前为「{status_name}」状态，不允许创建账号")

        # 3. 用户名：指定值优先，否则用企微 userid
        if username:
            username = username.strip()
        if not username:
            username = self._resolve_username(employee)

        # 检查指定的用户名是否可用
        existing = User.get_by_username(username)
        if existing:
            raise ValueError(f"用户名已存在: {username}")

        # 4. 使用默认密码（跳过强度验证，因为是临时密码）
        raw_password = generate_strong_password()
        password_hash = PasswordHelper.hash(raw_password, validate=False)

        # 5. 创建用户并分配"内部员工"角色（同步员工姓名）
        user = User.create_with_role(
            username=username,
            password_hash=password_hash,
            email=getattr(employee, 'email', None),
            phone=getattr(employee, 'mobile', None),
            name=getattr(employee, 'name', None),
            role_enum=UserRoleEnum.USER,
        )

        # 6. 标记首次登录需强制修改密码
        user.must_change_password = True
        user.save(commit=True)

        # 7. 关联员工 → 用户（账号状态从 User.is_active 推导，无需额外设置）
        employee.user_id = user.id
        employee.save(commit=True)

        logger.info(
            f"员工账号创建成功: employee={employee.name}(ID={employee_id}), "
            f"user={user.username}(ID={user.id}), 默认密码需首次登录修改"
        )

        return {
            "user_id": user.id,
            "username": user.username,
            "employee_id": employee_id,
            "employee_name": employee.name,
            "raw_password": raw_password
        }

    def _resolve_username(self, employee) -> str:
        """使用员工的企业微信 userid 作为登录名。"""
        wechat_user_id = getattr(employee, "enterprise_wechat_user_id", None)
        if wechat_user_id is not None:
            wechat_user_id = str(wechat_user_id).strip() or None
        if not wechat_user_id:
            raise ValueError("该员工没有企业微信 userid，请先同步通讯录后再创建账号")
        if len(wechat_user_id) > USERNAME_MAX_LEN:
            raise ValueError(
                f"企业微信 userid 超过 {USERNAME_MAX_LEN} 个字符，无法作为用户名: {wechat_user_id}"
            )
        return wechat_user_id
