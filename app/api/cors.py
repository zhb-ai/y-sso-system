"""动态 CORS 中间件

根据数据库中已注册应用的 redirect_uris 自动提取允许的 Origin，
无需手动维护 CORS 白名单。使用 TTL 缓存避免每次请求都查询数据库。

工作原理：

1. 每隔 cache_ttl（默认 5 分钟）从数据库查询所有激活应用的 redirect_uris，
   提取 scheme://host[:port] 作为允许的 Origin。

2. 例如应用管理中填写了 ``https://superset.example.com/oauth-authorized/y-sso``，
   则 ``https://superset.example.com`` 自动被允许跨域访问。

3. always_allow 中的地址（如开发前端 ``http://localhost:5173``）不依赖数据库，
   始终放行。

4. 数据库异常时自动回退到上次缓存的结果，不会影响正常服务。

使用示例::

    from app.api.cors import DynamicCORSMiddleware
    from app.domain.application.entities import Application

    app.add_middleware(
        DynamicCORSMiddleware,
        application_model=Application,
        cache_ttl=300,                          # 缓存 5 分钟
        always_allow=["http://localhost:5173"],  # 开发环境始终允许
    )
"""

import re
import time
import threading
from typing import Set, List, Optional
from urllib.parse import urlparse

from yweb.log import get_logger

logger = get_logger()

# localhost 任意端口的正则（匹配 http://localhost:xxxx 和 http://127.0.0.1:xxxx）
_LOCALHOST_RE = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$")


class DynamicCORSMiddleware:
    """动态 CORS 中间件（纯 ASGI 实现）

    从已注册应用的 redirect_uris 中提取允许的 Origin（scheme://host[:port]），
    仅放行匹配的跨域请求。

    使用纯 ASGI 而非 BaseHTTPMiddleware，避免 call_next 创建新任务上下文
    导致 ContextVar 隔离，进而引发 scoped_session 连接泄漏。

    特性：
    - TTL 缓存：默认 5 分钟刷新一次，应用增删后最多等一个缓存周期即可生效
    - always_allow：指定始终允许的 Origin 列表
    - allow_localhost：开发便利选项，允许 localhost / 127.0.0.1 任意端口
    - 异常容错：数据库查询失败时回退到上次缓存
    - OPTIONS 预检请求统一由中间件拦截，不会透传到路由（避免 405）
    """

    def __init__(
        self,
        app,
        application_model,
        cache_ttl: int = 300,
        always_allow: Optional[List[str]] = None,
        allow_localhost: bool = False,
    ):
        """
        Args:
            app: ASGI 应用
            application_model: Application ORM 模型类（需有 query、get_redirect_uris 方法）
            cache_ttl: 缓存有效期（秒），默认 300（5 分钟）
            always_allow: 始终允许的 Origin 列表（如 ["https://admin.example.com"]）
            allow_localhost: 是否允许 localhost / 127.0.0.1 任意端口（开发环境设为 True）
        """
        self.app = app
        self.application_model = application_model
        self.cache_ttl = cache_ttl
        self.always_allow: Set[str] = set(always_allow or [])
        self.allow_localhost = allow_localhost
        self._cached_origins: Set[str] = set()
        self._cache_time: float = 0
        self._refresh_lock = threading.Lock()

    def _extract_origin(self, uri: str) -> Optional[str]:
        """从 URI 中提取 origin（scheme://host[:port]）"""
        try:
            parsed = urlparse(uri)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            pass
        return None

    def _get_allowed_origins(self) -> Set[str]:
        """获取当前允许的 Origin 集合（带 TTL 缓存）

        使用锁防止缓存过期时多个并发请求同时查询数据库。
        """
        now = time.time()
        if now - self._cache_time < self.cache_ttl and self._cached_origins:
            return self._cached_origins

        if not self._refresh_lock.acquire(blocking=False):
            return self._cached_origins or self.always_allow

        try:
            if now - self._cache_time < self.cache_ttl and self._cached_origins:
                return self._cached_origins

            origins = set(self.always_allow)
            try:
                apps = self.application_model.query.filter_by(is_active=True).all()
                for app_entity in apps:
                    for uri in app_entity.get_redirect_uris():
                        origin = self._extract_origin(uri)
                        if origin:
                            origins.add(origin)

                self._cached_origins = origins
                self._cache_time = now
                logger.debug(f"CORS 允许的 Origins 已刷新: {origins}")
            except Exception as e:
                logger.warning(f"动态 CORS 查询失败，使用缓存: {e}")
                if self._cached_origins:
                    return self._cached_origins

            return origins
        finally:
            self._refresh_lock.release()

    def _is_origin_allowed(self, origin: str) -> bool:
        """判断 origin 是否被允许"""
        if self.allow_localhost and _LOCALHOST_RE.match(origin):
            return True
        return origin in self._get_allowed_origins()

    def _cors_headers_raw(self, origin: str) -> list:
        """构造 CORS 响应头（ASGI raw 格式）"""
        return [
            (b"access-control-allow-origin", origin.encode()),
            (b"access-control-allow-methods", b"GET, POST, PUT, DELETE, OPTIONS"),
            (b"access-control-allow-headers", b"Authorization, Content-Type, X-Requested-With"),
            (b"access-control-allow-credentials", b"true"),
            (b"access-control-max-age", b"600"),
        ]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        origin = None
        for key, value in scope.get("headers", []):
            if key == b"origin":
                origin = value.decode("latin-1")
                break

        if not origin:
            await self.app(scope, receive, send)
            return

        is_allowed = self._is_origin_allowed(origin)

        # 预检请求（OPTIONS）— 统一拦截，不透传到路由
        method = scope.get("method", "")
        if method == "OPTIONS":
            if is_allowed:
                headers = self._cors_headers_raw(origin)
            else:
                headers = []
            status = 200 if is_allowed else 204
            await send({
                "type": "http.response.start",
                "status": status,
                "headers": headers,
            })
            await send({"type": "http.response.body", "body": b""})
            return

        # 正常请求：如果 origin 被允许，注入 CORS 响应头
        if is_allowed:
            cors_headers = self._cors_headers_raw(origin)

            async def send_with_cors(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.extend(cors_headers)
                    message = {**message, "headers": headers}
                await send(message)

            await self.app(scope, receive, send_with_cors)
        else:
            await self.app(scope, receive, send)
