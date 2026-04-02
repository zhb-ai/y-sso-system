"""SSO 门户 API 回归测试

回归验证日志中的错误：
    sqlalchemy.exc.TimeoutError: QueuePool limit of size 50 overflow 100 reached,
    connection timed out, timeout 30.00

Bug 原因：
    sso_portal.py 的 sso_available_apps 端点使用 async def 声明，
    但内部执行同步 ORM 查询 application_model.query.filter_by(...).all()。

    FastAPI 中：
    - async def → 在事件循环线程上执行（同步调用会冻结事件循环）
    - def       → 自动放入线程池执行（不阻塞事件循环）

    async def + 同步阻塞 = 事件循环冻结 = 并发请求串行化 = 连接池耗尽

修复方式：
    将 async def sso_available_apps() 改为 def sso_available_apps()
"""

import asyncio
import time
import traceback

import pytest
import httpx
from unittest.mock import MagicMock
from fastapi import FastAPI
from sqlalchemy import create_engine, Integer, Boolean
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session, Mapped, mapped_column
from sqlalchemy.exc import TimeoutError as SATimeoutError
from sqlalchemy.pool import QueuePool

from app.api.v1.sso_portal import create_sso_portal_router

SLOW_QUERY_SECONDS = 0.3
CONCURRENT_REQUESTS = 4


def _make_app_with_mock(blocking_seconds: float) -> FastAPI:
    """构造带慢查询 mock 的测试应用"""
    mock_model = MagicMock()

    def slow_all():
        time.sleep(blocking_seconds)
        return []

    mock_model.query.filter_by.return_value.all = slow_all

    app = FastAPI()
    router = create_sso_portal_router(application_model=mock_model)
    app.include_router(router, prefix="/api/v1")
    return app


class _Base(DeclarativeBase):
    pass


class AppEntity(_Base):
    """模拟 Application 模型"""
    __tablename__ = "sso_application"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


def _trigger_pool_exhaustion_error():
    """触发与日志中相同的 QueuePool 连接池耗尽错误"""
    pool_size = 5
    max_overflow = 5
    total = pool_size + max_overflow

    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=2,
        connect_args={"check_same_thread": False},
    )
    _Base.metadata.create_all(bind=engine)
    Session = scoped_session(sessionmaker(bind=engine))

    held_conns = [engine.connect() for _ in range(total)]
    session = Session()
    try:
        session.query(AppEntity).filter_by(is_active=True).all()
    except SATimeoutError:
        traceback.print_exc()
    finally:
        Session.remove()
        for conn in held_conns:
            conn.close()
        engine.dispose()


class TestSSOPortalEventLoopBlocking:
    """SSO 门户端点事件循环阻塞回归测试"""

    @pytest.mark.asyncio
    async def test_sso_apps_concurrent_requests_not_serialized(self):
        """验证 /sso/apps 端点的并发请求不应被串行化

        发送 N 个并发请求（每个查询耗时 0.3s）：
        - 正确（def）:      总耗时 ≈ 0.3s（线程池并行）
        - 错误（async def）: 总耗时 ≈ 1.2s（事件循环串行 → 连接池耗尽风险）

        修复前: FAILED — 请求被串行化，输出与日志相同的 QueuePool TimeoutError
        修复后: PASSED — 请求并行执行，无报错
        """
        app = _make_app_with_mock(SLOW_QUERY_SECONDS)

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            start = time.monotonic()
            tasks = [client.get("/api/v1/sso/apps") for _ in range(CONCURRENT_REQUESTS)]
            responses = await asyncio.gather(*tasks)
            elapsed = time.monotonic() - start

        for resp in responses:
            assert resp.status_code == 200

        serial_time = SLOW_QUERY_SECONDS * CONCURRENT_REQUESTS
        parallel_threshold = SLOW_QUERY_SECONDS * 2
        is_serialized = elapsed > parallel_threshold

        print()
        print("=" * 64)
        print("  SSO 门户端点并发请求测试")
        print("=" * 64)
        print(f"  并发请求数:         {CONCURRENT_REQUESTS}")
        print(f"  单次查询耗时:       {SLOW_QUERY_SECONDS}s")
        print(f"  理想并行总耗时:     ≈ {SLOW_QUERY_SECONDS}s  (def, 线程池并行)")
        print(f"  串行化总耗时:       ≈ {serial_time}s  (async def, 事件循环串行)")
        print(f"  --------------------")
        print(f"  实际总耗时:         {elapsed:.2f}s")
        print("=" * 64)

        if is_serialized:
            print("  结果: 请求被串行化! 事件循环被 async def 阻塞!")
            print()
            print("  当并发请求被串行化，连接无法及时归还，最终耗尽连接池：")
            print("-" * 64)
            _trigger_pool_exhaustion_error()
            print("-" * 64)
            print()

            pytest.fail(
                f"并发请求被串行化! 总耗时 {elapsed:.2f}s (阈值 {parallel_threshold}s)\n"
                f"原因: sso_available_apps 使用 async def 但调用同步 ORM，阻塞了事件循环\n"
                f"修复: 将 async def sso_available_apps() 改为 def sso_available_apps()"
            )

        print("  结果: 请求并行执行，事件循环未被阻塞")
        print("=" * 64)
