"""DashboardAppService 测试"""

from app.services.dashboard_app import DashboardAppService


class ComparableField:
    """支持比较表达式的简易字段桩"""

    def __ge__(self, other):
        return ("ge", other)


class CountQuery:
    """返回固定 count 的查询桩"""

    def __init__(self, count):
        self._count = count

    def count(self):
        return self._count


class UserQuery(CountQuery):
    """用户查询桩，区分总数和活跃数"""

    def __init__(self, total_count, active_count):
        super().__init__(total_count)
        self._active_count = active_count

    def filter(self, *_args, **_kwargs):
        return CountQuery(self._active_count)


class UserModelStub:
    """用户模型桩"""

    last_login_at = ComparableField()
    query = UserQuery(total_count=20, active_count=10)


class ApplicationModelStub:
    """应用模型桩"""

    query = CountQuery(3)


class TestDashboardAppService:
    """DashboardAppService 行为测试"""

    def test_get_statistics_returns_daily_active_and_total_user_count(self):
        """统计数据应同时包含日活用户数和总用户数"""
        service = DashboardAppService(
            user_model=UserModelStub,
            application_model=ApplicationModelStub,
        )

        stats = service.get_statistics()

        assert stats["user_count"] == 10
        assert stats["total_user_count"] == 20
        assert stats["application_count"] == 3
