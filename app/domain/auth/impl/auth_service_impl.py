"""认证服务实现

继承 yweb.auth.BaseAuthService，获得开箱即用的标准认证流程。

框架已自动处理：
- 用户名密码认证、JWT 令牌创建/验证/刷新
- 登录成功记录（update_last_login）
- 登录失败记录（on_authenticate_failure，含具体失败原因）
- 令牌撤销、用户锁定/解锁

项目扩展：
- authenticate: 在框架认证基础上，额外检查员工组织关联状态
  （离职员工即使 User 账号未及时禁用，也无法登录）
"""

from typing import Optional

from yweb.auth import BaseAuthService
from yweb.log import get_logger

logger = get_logger()


class AuthServiceImpl(BaseAuthService):
    """项目认证服务实现

    继承 BaseAuthService 获得全部标准认证能力。

    扩展点：
    - authenticate: 额外检查员工组织关联状态（双重防护）
    """

    def authenticate(self, username: str, password: str) -> Optional[object]:
        """认证用户（含员工状态检查）

        在框架标准认证（用户名密码 + is_active 检查）基础上，
        额外检查用户关联的员工是否为离职状态。

        双重防护：
        1. 同步层：员工离职时已自动禁用 User.is_active（第一道）
        2. 认证层：即使 User.is_active 未及时更新，员工状态检查也会拦截（第二道）

        Args:
            username: 用户名
            password: 明文密码

        Returns:
            认证成功返回用户对象，失败返回 None
        """
        # 框架标准认证（用户名密码 + is_active + 锁定检查）
        user = super().authenticate(username, password)
        if user is None:
            return None

        # 额外检查：员工组织关联状态
        if not self._check_employee_status(user):
            return None

        return user

    def _check_employee_status(self, user) -> bool:
        """检查用户关联的员工是否为离职状态

        查找所有通过 Employee.user_id 关联到此 User 的员工，
        检查其 EmployeeOrgRel 是否全部为离职状态。

        规则：
        - 用户无关联员工 → 允许登录（纯后台用户，如 admin）
        - 有员工关联且至少一个非离职 → 允许登录
        - 有员工关联但全部离职 → 拒绝登录

        Returns:
            True 允许登录，False 拒绝
        """
        try:
            from yweb.organization import EmployeeStatus

            # 查找关联此 User 的 Employee（通过 user_id 字段）
            # 优先使用 setup_organization 创建的模型（Web 场景），避免 ensure_dynamic_models 重复创建导致 "Multiple classes found for path Department"
            from app.models_registry import get_app_org_models, ensure_dynamic_models
            org_models = get_app_org_models()
            if org_models is not None:
                Employee = org_models.Employee
                EmployeeOrgRel = org_models.EmployeeOrgRel
            else:
                registry = ensure_dynamic_models()
                Employee = registry.org_models.Employee
                EmployeeOrgRel = registry.org_models.EmployeeOrgRel

            # 查找 Employee.user_id == user.id 的记录
            employees = Employee.query.filter(
                Employee.user_id == user.id,
            ).all()

            if not employees:
                return True  # 无关联员工（纯后台用户），允许登录

            # 检查每个员工的组织关联状态
            for emp in employees:
                rels = EmployeeOrgRel.query.filter(
                    EmployeeOrgRel.employee_id == emp.id,
                ).all()
                for rel in rels:
                    if hasattr(rel, 'status') and rel.status != EmployeeStatus.RESIGNED.value:
                        return True  # 至少有一个非离职的组织关联，允许登录

            # 所有员工的所有组织关联都是离职状态
            logger.info(
                f"认证拒绝: 用户 '{user.username}' 关联的员工均已离职"
            )
            return False

        except Exception as e:
            # 检查失败不阻断登录（容错：组织模块未初始化等情况）
            logger.warning(f"员工状态检查异常，跳过: {e}")
            return True
