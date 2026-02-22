"""员工账号 - 应用服务层

跨域服务：衔接组织架构域（Employee）和认证域（User），
处理员工自动创建用户账号的业务逻辑。
"""

import re
from typing import Type

from pypinyin import lazy_pinyin, Style
from yweb.auth import PasswordHelper
from yweb.log import get_logger

from app.domain.auth.model.user import User, UserRoleEnum

logger = get_logger()

# 员工账号默认密码（首次登录需强制修改）
DEFAULT_PASSWORD = "000000"


def _name_to_pinyin(name: str) -> str:
    """将中文姓名转为拼音用户名

    规则：
    - 中文姓名 → 全拼小写无空格（张三 → zhangsan）
    - 已是纯 ASCII → 直接小写（John → john）
    - 混合内容 → 去除非字母数字字符后拼接

    Returns:
        拼音字符串，如果转换失败返回空字符串
    """
    if not name or not name.strip():
        return ""

    name = name.strip()

    # 纯 ASCII 名（英文名等），直接小写 + 去空格
    if all(ord(c) < 128 for c in name):
        result = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
        return result if len(result) >= 2 else ""

    # 含中文：转拼音
    py_list = lazy_pinyin(name, style=Style.NORMAL)
    result = ''.join(py_list).lower()
    # 去除非字母数字
    result = re.sub(r'[^a-z0-9]', '', result)
    return result if len(result) >= 2 else ""


def _generate_unique_username(base: str, max_attempts: int = 100) -> str:
    """基于 base 生成唯一用户名，冲突时追加数字后缀

    Args:
        base: 基础用户名
        max_attempts: 最大尝试次数

    Returns:
        可用的唯一用户名

    Raises:
        ValueError: 无法生成唯一用户名
    """
    # 先试原名
    if not User.get_by_username(base):
        return base

    # 追加数字后缀
    for i in range(1, max_attempts + 1):
        candidate = f"{base}{i}"
        if not User.get_by_username(candidate):
            return candidate

    raise ValueError(f"无法生成唯一用户名（基于 {base}）")


class EmployeeAccountService:
    """员工账号服务

    为员工自动创建/关联内部用户账号：
    - 自动生成用户名（姓名拼音，如张三 → zhangsan，同名冲突 → zhangsan1）
    - 默认密码 000000，首次登录强制修改
    - 分配"内部员工"角色
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

        # 3. 生成用户名
        if not username:
            username = self._resolve_username(employee)

        # 检查指定的用户名是否可用
        existing = User.get_by_username(username)
        if existing:
            raise ValueError(f"用户名已存在: {username}")

        # 4. 使用默认密码（跳过强度验证，因为是临时密码）
        raw_password = DEFAULT_PASSWORD
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
        }

    def _resolve_username(self, employee) -> str:
        """根据员工信息自动推导用户名

        优先级：姓名拼音 > emp_员工ID
        示例：张三 → zhangsan，同名冲突 → zhangsan1
        """
        # 优先使用姓名拼音
        name = getattr(employee, 'name', None)
        if name:
            pinyin_name = _name_to_pinyin(name)
            if pinyin_name:
                return _generate_unique_username(pinyin_name)

        # 兜底：emp_员工ID
        return _generate_unique_username(f"emp_{employee.id}")
