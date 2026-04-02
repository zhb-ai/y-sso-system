"""验证 yweb-core 异步安全检测在 y-sso-system 中的实际效果

测试场景：
    1. async def 路由直接调用 ORM → 收到 SynchronousOnlyOperation (HTTP 500)
    2. def 路由直接调用 ORM → 正常返回 (HTTP 200)
    3. async def 路由 + run_db() → 正常返回 (HTTP 200)

验证目标：
    确认 yweb-core 的防御性设计（async 安全检测）在业务项目中正常工作，
    当开发者误用 async def + 同步 ORM 时能立即收到清晰的错误提示。
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from yweb.orm import (
    init_database,
    BaseModel,
    run_db,
    SynchronousOnlyOperation,
    db_manager,
)


class _TestUser(BaseModel):
    """测试用模型"""
    __tablename__ = "async_safety_test_user"
    username: Mapped[str] = mapped_column(String(50), default="")


@pytest.fixture(scope="module")
def test_app():
    """构造一个包含三种路由模式的测试 FastAPI 应用"""
    engine, _ = init_database("sqlite:///:memory:")
    BaseModel.metadata.create_all(bind=engine)

    with db_manager.get_session() as session:
        pass
    from yweb.orm import db_session_scope
    with db_session_scope() as session:
        session.add(_TestUser(name="张三", username="zhangsan"))
        session.add(_TestUser(name="李四", username="lisi"))

    app = FastAPI()

    # ❌ 场景1：async def 直接调用同步 ORM（应被拦截）
    @app.get("/bad-async")
    async def bad_async_route():
        users = _TestUser.query.all()
        return {"count": len(users)}

    # ✅ 场景2：def 路由（FastAPI 自动放线程池）
    @app.get("/good-sync")
    def good_sync_route():
        users = _TestUser.query.all()
        return {"count": len(users)}

    # ✅ 场景3：async def + run_db()
    @app.get("/good-async")
    async def good_async_route():
        users = await run_db(_TestUser.get_all)
        return {"count": len(users)}

    # ✅ 场景4：async def + run_db() + lambda 复杂查询
    @app.get("/good-async-lambda")
    async def good_async_lambda_route():
        users = await run_db(
            lambda: _TestUser.query.filter_by(username="zhangsan").all()
        )
        return {"count": len(users), "name": users[0].name if users else ""}

    yield app

    BaseModel.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(test_app):
    return TestClient(test_app, raise_server_exceptions=False)


class TestAsyncSafetyInSSOSystem:
    """验证异步安全检测在 y-sso-system 业务项目中的实际效果"""

    def test_async_route_direct_orm_returns_500(self, client):
        """async def 路由直接调用 ORM → 应返回 500 错误

        这就是之前导致 QueuePool TimeoutError 的写法，
        现在 yweb-core 会在阻塞事件循环之前直接拦截并抛出异常。
        """
        resp = client.get("/bad-async")

        assert resp.status_code == 500, (
            f"期望 500，实际 {resp.status_code}。"
            "async def 中直接调用 ORM 应触发 SynchronousOnlyOperation"
        )
        print()
        print("=" * 64)
        print("  ✅ async def + 直接 ORM 调用 → 500 异常（防御检测生效）")
        print(f"  响应状态码: {resp.status_code}")
        print("=" * 64)

    def test_sync_route_works_normally(self, client):
        """def 路由直接调用 ORM → 正常返回 200"""
        resp = client.get("/good-sync")

        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        print()
        print("=" * 64)
        print("  ✅ def 路由 + 直接 ORM 调用 → 200 正常（FastAPI 线程池）")
        print(f"  返回数据: {data}")
        print("=" * 64)

    def test_async_route_with_run_db_works(self, client):
        """async def + run_db() → 正常返回 200"""
        resp = client.get("/good-async")

        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        print()
        print("=" * 64)
        print("  ✅ async def + run_db() → 200 正常（线程池安全包装）")
        print(f"  返回数据: {data}")
        print("=" * 64)

    def test_async_route_with_run_db_lambda_works(self, client):
        """async def + run_db(lambda: ...) 复杂查询 → 正常返回 200"""
        resp = client.get("/good-async-lambda")

        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["name"] == "张三"
        print()
        print("=" * 64)
        print("  ✅ async def + run_db(lambda) → 200 正常（复杂查询）")
        print(f"  返回数据: {data}")
        print("=" * 64)


class TestSynchronousOnlyOperationException:
    """直接验证异常类型和错误信息"""

    def test_exception_is_runtime_error(self):
        """SynchronousOnlyOperation 是 RuntimeError 的子类"""
        assert issubclass(SynchronousOnlyOperation, RuntimeError)

    @pytest.mark.asyncio
    async def test_direct_orm_in_async_raises_exception(self):
        """在 async 函数中直接调用 ORM → 抛出 SynchronousOnlyOperation"""
        with pytest.raises(SynchronousOnlyOperation) as exc_info:
            _TestUser.query.all()

        error_msg = str(exc_info.value)
        assert "async" in error_msg or "事件循环" in error_msg
        assert "run_db" in error_msg or "def" in error_msg

        print()
        print("=" * 64)
        print("  ✅ 异常信息验证:")
        print("-" * 64)
        for line in error_msg.split("\n")[:8]:
            print(f"  {line}")
        print("  ...")
        print("=" * 64)
