"""按用户名读取员工花名册快照。"""

from typing import Any, Type

from app.domain.auth.model.user import User


def get_hr_roster_by_username(employee_model: Type, username: str) -> dict[str, Any]:
    """用 user.username 找到关联员工的花名册快照。

    用户页上的「用户名」对应 user.username。创建账号时默认等于企微 userid，
    也可以另行指定，因此不能把用户名直接当作企微 userid。
    """
    username = (username or "").strip()
    if not username:
        raise ValueError("用户名不能为空")

    user = User.get_by_username(username)
    if user is None:
        raise ValueError(f"用户不存在: {username}")

    employee = employee_model.query.filter(
        employee_model.user_id == user.id
    ).first()
    if employee is None:
        raise ValueError(f"用户未关联员工: {username}")
    if not employee.hr_roster:
        raise ValueError(f"该员工还没有花名册数据: {username}")

    return {
        "username": user.username,
        "employee_id": employee.id,
        "hr_roster": employee.hr_roster,
    }
