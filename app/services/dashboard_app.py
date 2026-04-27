"""仪表盘 - 应用服务层

跨聚合查询服务：汇总各业务模块的统计数据。
"""

from datetime import datetime, timedelta

from yweb.log import get_logger

logger = get_logger()


class DashboardAppService:
    """仪表盘统计服务

    从多个聚合（User、Application、Employee、Department）
    查询统计数据，提供系统概览。
    """

    def __init__(self, user_model, application_model, org_models=None):
        """
        Args:
            user_model: 用户模型类
            application_model: 应用模型类
            org_models: 组织架构模型容器（OrgModels），可选
        """
        self.user_model = user_model
        self.application_model = application_model
        self.org_models = org_models

    def get_statistics(self) -> dict:
        """获取系统概览统计

        Returns:
            包含 application_count, user_count, total_user_count, employee_count, department_count 的字典
            user_count: 过去24小时内活跃用户数（基于 last_login_at 筛选）
            total_user_count: 系统总用户数
        """
        since = datetime.now() - timedelta(hours=24)
        daily_active_count = (
            self.user_model.query
            .filter(self.user_model.last_login_at >= since)
            .count()
        )
        total_user_count = self.user_model.query.count()
        stats = {
            "application_count": self.application_model.query.count(),
            "user_count": daily_active_count,
            "total_user_count": total_user_count,
            "employee_count": 0,
            "department_count": 0,
        }

        if self.org_models is not None:
            try:
                stats["employee_count"] = self.org_models.Employee.query.count()
            except Exception as e:
                logger.warning(f"获取员工数量失败: {e}")

            try:
                stats["department_count"] = self.org_models.Department.query.count()
            except Exception as e:
                logger.warning(f"获取部门数量失败: {e}")

        return stats
