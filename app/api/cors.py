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
from typing import Set, List, Optional
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from yweb.log import get_logger

logger = get_logger()

# localhost 任意端口的正则（匹配 http://localhost:xxxx 和 http://127.0.0.1:xxxx）
_LOCALHOST_RE = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$")


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    """动态 CORS 中间件

    从已注册应用的 redirect_uris 中提取允许的 Origin（scheme://host[:port]），
    仅放行匹配的跨域请求。

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
        super().__init__(app)
        self.application_model = application_model
        self.cache_ttl = cache_ttl
        self.always_allow: Set[str] = set(always_allow or [])
        self.allow_localhost = allow_localhost
        self._cached_origins: Set[str] = set()
        self._cache_time: float = 0

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
        """获取当前允许的 Origin 集合（带 TTL 缓存）"""
        now = time.time()
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
            # 数据库查询失败时回退到上次缓存
            logger.warning(f"动态 CORS 查询失败，使用缓存: {e}")
            if self._cached_origins:
                return self._cached_origins

        return origins

    def _is_origin_allowed(self, origin: str) -> bool:
        """判断 origin 是否被允许"""
        # 1. localhost 开发模式：任意端口放行
        if self.allow_localhost and _LOCALHOST_RE.match(origin):
            return True
        # 2. 精确匹配 always_allow + 数据库来源
        return origin in self._get_allowed_origins()

    def _cors_headers(self, origin: str) -> dict:
        """构造 CORS 响应头"""
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Requested-With",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "600",
        }

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")

        # 无 Origin 头 — 非跨域请求，直接放行
        if not origin:
            return await call_next(request)

        is_allowed = self._is_origin_allowed(origin)

        # 预检请求（OPTIONS）— 统一由中间件拦截，绝不透传到路由
        if request.method == "OPTIONS":
            if is_allowed:
                return Response(status_code=200, headers=self._cors_headers(origin))
            else:
                # Origin 不允许：返回 204 无 CORS 头，浏览器会自动阻止后续请求
                return Response(status_code=204)

        # 正常请求
        response = await call_next(request)

        # 添加 CORS 响应头
        if is_allowed:
            for key, value in self._cors_headers(origin).items():
                response.headers[key] = value

        return response
