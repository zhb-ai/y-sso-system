"""员工账号管理 API

为员工创建内部用户账号的项目级端点。
属于跨域操作（组织架构 + 认证），独立于 yweb-core 的员工 CRUD。

端点列表：
    POST /org/employee/create-account  → 为员工创建用户账号
"""

from typing import Optional, Type

from fastapi import APIRouter
from pydantic import BaseModel, Field

from yweb import DTO
from yweb.response import Resp, ItemResponse

from app.services.employee_app import EmployeeAccountService


def create_employee_account_router(employee_model: Type) -> APIRouter:
    """创建员工账号管理路由

    Args:
        employee_model: 员工模型类（由 setup_organization 创建）

    Returns:
        APIRouter
    """

    router = APIRouter()
    account_service = EmployeeAccountService(employee_model=employee_model)

    # ==================== DTO ====================

    class CreateAccountRequest(BaseModel):
        """创建员工账号请求"""
        employee_id: int = Field(..., description="员工ID")
        username: Optional[str] = Field(None, description="指定用户名（不传则自动生成）")

    class AccountCreatedResponse(DTO):
        """账号创建结果"""
        user_id: int = 0
        username: str = ""
        employee_id: int = 0
        employee_name: str = ""
        raw_password: str = ""

    # ==================== 端点 ====================

    @router.post(
        "/org/employee/create-account",
        response_model=ItemResponse[AccountCreatedResponse],
        summary="为员工创建用户账号",
        description=(
            "自动为员工创建内部用户账号并关联。\n"
            "用户名生成优先级：指定 > 手机号 > 邮箱前缀 > emp_员工ID。\n"
            "默认密码为 000000，首次登录时强制修改。\n"
            "创建后自动分配「内部员工」角色。"
        ),
    )
    def create_employee_account(data: CreateAccountRequest):
        """为员工创建用户账号"""
        try:
            user_info = account_service.create_account_for_employee(
                employee_id=data.employee_id,
                username=data.username,
            )
            return Resp.OK(
                AccountCreatedResponse(
                    user_id=user_info["user_id"],
                    username=user_info["username"],
                    employee_id=user_info["employee_id"],
                    employee_name=user_info["employee_name"],
                    raw_password=user_info["raw_password"],
                ),
                message=f"账号创建成功，默认密码 {user_info['raw_password']}，首次登录需修改",
            )
        except ValueError as e:
            return Resp.BadRequest(message=str(e))

    return router
