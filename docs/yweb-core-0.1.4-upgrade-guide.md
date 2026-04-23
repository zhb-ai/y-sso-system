# yweb-core 0.1.3 → 0.1.4 升级指南（SSO 项目）

> 适用范围：y-sso-system（单点登录系统）从 yweb 0.1.3 升级到 0.1.4。
>
> 本文包含三部分：变更摘要（对项目的影响）、SSO 项目内已完成的代码改动清单、开发/服务器升级步骤与回滚预案。

---

## 一、yweb-core 0.1.4 关键变更摘要

### 1. 破坏性变更

#### 1.1 `run_db` 重命名为 `async_db_call`，旧别名已**彻底移除**

0.1.4 先将 `run_db` 重命名为 `async_db_call` 并保留了 deprecated 别名，随后在发布前彻底删除了旧别名。任何仍在导入 `run_db` 的代码都会立即 `ImportError`。

```python
# ❌ 0.1.3 写法
from yweb.orm import run_db
users = await run_db(User.get_all)

# ✅ 0.1.4 写法
from yweb.orm import async_db_call
users = await async_db_call(User.get_all)
```

#### 1.2 新增 async 安全检测：在事件循环中访问 `Model.query` 会抛 `SynchronousOnlyOperation`

0.1.4 将 `CoreModel.query` 属性包装为 `AsyncSafeQueryProperty`，并在 `db_manager.get_session()` 入口也插入了检测。效果如下：

| 调用场景 | 行为 |
|---|---|
| `def` 路由（FastAPI 自动放线程池） | ✅ 放行 |
| `async def` 路由 + `await async_db_call(...)` | ✅ 放行 |
| `async def` 路由 + 直接 `Model.query.xxx()` | ❌ 抛 `SynchronousOnlyOperation` |
| `async def` 体内使用 `with allow_sync():` | ✅ 放行（仅适用于 lifespan / 启动初始化） |
| `with db_session_scope():` / `@with_db_session` | ✅ 放行（内部自动 `allow_sync`） |
| 普通线程 / 测试 / 定时任务 | ✅ 放行 |

检测行为可通过环境变量调整（**不建议生产环境降级**）：

```bash
YWEB_ASYNC_SAFETY=error  # 默认，抛异常
YWEB_ASYNC_SAFETY=warn   # 仅发 RuntimeWarning
YWEB_ASYNC_SAFETY=off    # 关闭检测
```

#### 1.3 `HybridQuery` 先引入后撤除

0.1.4 开发过程中曾引入 `HybridQuery`（允许 `await User.query.all()` 语法），后因设计权衡撤除。当前最终方案统一使用 `async_db_call()`。任何依赖 `HybridQuery` / `_HybridTerminal` 的代码需要回退到 `async_db_call`。

### 2. 新增能力

- `allow_sync()` 上下文管理器：合法的 async + 同步 ORM 场景（如 FastAPI `lifespan` 内的一次性初始化）可用它临时放行检测。
- `db_session_scope()` / `@with_db_session` 内部自动启用 `allow_sync`。
- 新增 `slowapi` 限流模块为可选依赖（SSO 暂未启用）。
- `JWTManager` 支持自定义 `kid` header（SSO 暂未使用）。

### 3. Bug 修复

- 修复 `with_db_session` 在 async 函数中同步调用的问题。
- 修复 OIDC `userinfo` 路由与真实 `OidcManager` 接口不一致。
- 修复 auth mixins 在 SQLite / MySQL 上的时区比较 `TypeError`。
- ORM pk_generator 在 async 上下文中的死循环。
- `db_session_scope` 在 async 上下文下自动 `allow_sync`。

---

## 二、SSO 项目内完成的代码改动清单

本次升级在本仓库共改动 5 个文件。每处改动都是为了兼容 0.1.4 的 async 安全检测；业务语义未变化。

### 2.1 `requirements.txt`

yweb 0.1.4 已发布到 [PyPI](https://pypi.org/project/yweb/0.1.4/)，改为从 PyPI 直接安装，比 git 方式更快、无需网络访问 GitHub：

```diff
- yweb @ git+https://github.com/yafo-ai/yweb-core.git@0.1.3
+ yweb==0.1.4
```

### 2.2 `app/api/dependencies.py` — 权限依赖改为同步 `def`

`_require_admin` 与 `_require_permission` 只做同步 ORM / 属性访问，没有 `await` 任何异步 I/O。改为 `def` 后，FastAPI 会自动把依赖放入线程池执行，不会触发 async 检测。

```diff
-    async def _require_admin(user=Depends(auth.get_current_user)):
+    def _require_admin(user=Depends(auth.get_current_user)):
         if not hasattr(user, 'has_role') or not user.has_role('admin'):
             ...
```

```diff
-    async def _require_permission(user=Depends(auth.get_current_user)):
+    def _require_permission(user=Depends(auth.get_current_user)):
         # admin 直接放行
         if hasattr(user, 'has_role') and user.has_role('admin'):
             ...
         user_perms = RolePermission.get_permissions_by_role_ids(role_ids)
```

### 2.3 `app/api/v1/wechat_work.py` — 企微 Webhook 用 `async_db_call` 包装同步 ORM

`receive_webhook` 必须保留 `async def`（因需要 `await request.body()`）。把读取 body 之后的同步 ORM 逻辑抽成本地函数 `_handle_callback_sync`，用 `await async_db_call(...)` 一次性推入线程池：

```diff
 from yweb.response import Resp, OkResponse
 from yweb.log import get_logger
+from yweb.orm import async_db_call
```

```diff
         try:
-            org = _get_wechat_org(org_id)
-            handler = _build_webhook_handler(org)
-
             body = await request.body()
             body_str = body.decode("utf-8")
-
-            handler.handle_callback(
-                org, msg_signature, timestamp, nonce, body_str,
-            )
+
+            def _handle_callback_sync():
+                org = _get_wechat_org(org_id)
+                handler = _build_webhook_handler(org)
+                handler.handle_callback(
+                    org, msg_signature, timestamp, nonce, body_str,
+                )
+
+            await async_db_call(_handle_callback_sync)
         except Exception as e:
             ...
```

### 2.4 `app/api/cors.py` — 动态 CORS 缓存刷新异步化

`DynamicCORSMiddleware.__call__` 是 ASGI `async def`，每个请求都会命中。原实现在 `_get_allowed_origins()` 中直接访问 `Application.query.filter_by(...).all()`，缓存过期时会触发 `SynchronousOnlyOperation`。

重构方式：

1. 新增 `_refresh_origins_sync()`：纯同步，承接原来的 DB 查询 + 加锁逻辑。
2. 新增 `_ensure_origins_fresh()`：async 方法，命中缓存时零开销；过期时 `await async_db_call(self._refresh_origins_sync)`。
3. `_is_origin_allowed()` 退化为纯内存判断。
4. 在 `__call__` 里先 `await self._ensure_origins_fresh()` 再做判断。

```diff
 from yweb.log import get_logger
+from yweb.orm import async_db_call
```

```diff
-    def _get_allowed_origins(self) -> Set[str]:
-        ...
-        apps = self.application_model.query.filter_by(is_active=True).all()
-        ...
-
-    def _is_origin_allowed(self, origin: str) -> bool:
-        if self.allow_localhost and _LOCALHOST_RE.match(origin):
-            return True
-        return origin in self._get_allowed_origins()
+    def _refresh_origins_sync(self) -> Set[str]:
+        """同步刷新允许的 Origin 集合（在线程池中执行，内含 DB 查询）"""
+        ...
+        apps = self.application_model.query.filter_by(is_active=True).all()
+        ...
+
+    async def _ensure_origins_fresh(self) -> None:
+        """缓存过期时异步触发一次刷新；命中缓存时零开销"""
+        now = time.time()
+        if now - self._cache_time < self.cache_ttl and self._cached_origins:
+            return
+        await async_db_call(self._refresh_origins_sync)
+
+    def _is_origin_allowed(self, origin: str) -> bool:
+        """判断 origin 是否被允许（纯内存判断，调用前须保证缓存已刷新）"""
+        if self.allow_localhost and _LOCALHOST_RE.match(origin):
+            return True
+        return origin in (self._cached_origins or self.always_allow)
```

```diff
         if not origin:
             await self.app(scope, receive, send)
             return
 
+        await self._ensure_origins_fresh()
         is_allowed = self._is_origin_allowed(origin)
```

### 2.5 `tests/test_api/test_async_safety_integration.py` — 同步测试与新符号

- `from yweb.orm import ... run_db ...` → `async_db_call`；
- 所有 `await run_db(...)` 调用替换为 `await async_db_call(...)`；
- `TestSynchronousOnlyOperationException.test_direct_orm_in_async_raises_exception` 改回断言：直接访问 `Model.query` 立即抛 `SynchronousOnlyOperation`，并检查异常消息包含修复指引（移除 `_HybridTerminal` 相关断言）。

测试全部通过：

```
tests/test_api/test_async_safety_integration.py ...... [6 passed]
tests/ ............................. [45 passed, 0 failed]
```

---

## 三、开发环境升级步骤

```powershell
# 1. 拉取最新代码
git pull

# 2. 激活 venv（以 PowerShell 为例）
.\venv\Scripts\Activate.ps1

# 3. 升级依赖
pip install -r requirements.txt

# 4. 运行测试
pytest

# 5. 启动服务
python dev_server.py
```

### 冒烟检查清单

- [ ] 访问 `http://localhost:8000/docs` 打开 Swagger，确认 API 能正常列出。
- [ ] 登录并获取 token（`/api/v1/auth/login`）。
- [ ] 调用任意带 `require_permission` 的管理接口（如 `GET /api/v1/users`），返回 200。
- [ ] 首次从前端管理后台打开页面，观察后端日志是否出现 `SynchronousOnlyOperation`——应当没有。
- [ ] 若项目启用了企微 webhook，手动 POST 一个错误签名的回调，确认响应为 `success` 且错误只在日志中记录。

---

## 四、服务器升级指南（生产 / 测试环境）

> 本节假设 SSO 采用「venv + uvicorn + systemd/supervisor」部署模式。若用 Docker/K8s 部署，请把对应步骤换成构建新镜像 → 滚动发布。

### 4.1 升级前准备

1. **通知相关方**：确定维护窗口。接入 SSO 的下游系统在升级期间登录会短暂中断。
2. **备份数据库**：
   ```bash
   # SQLite
   cp app/db/y_sso.db app/db/y_sso.db.bak-$(date +%Y%m%d%H%M)

   # MySQL / PostgreSQL 请使用对应的 mysqldump / pg_dump
   ```
3. **备份配置与 venv**（便于回滚）：
   ```bash
   cp -r config config.bak-$(date +%Y%m%d%H%M)
   cp -r venv venv.bak-$(date +%Y%m%d%H%M)   # 可选，体积较大时可跳过
   ```
4. **确认当前 yweb 版本**：
   ```bash
   ./venv/bin/pip show yweb | grep Version
   ```
5. **确认服务器可访问 PyPI**（默认从 `https://pypi.org` 安装；如使用内网镜像，确认镜像已同步到 `yweb==0.1.4`）。

### 4.2 升级执行

```bash
# 1. 停服
sudo systemctl stop y-sso        # 或 supervisorctl stop y-sso / docker compose stop

# 2. 拉代码
cd /opt/y-sso-system             # 实际部署目录
git fetch --all
git checkout <release-tag-or-branch>
git pull

# 3. 激活 venv 并升级依赖
source venv/bin/activate
pip install -r requirements.txt

# 4. 验证 yweb 版本已升到 0.1.4
pip show yweb | grep Version     # 期望 Version: 0.1.4

# 5. 检查数据库迁移（本次升级不包含表结构变更，预期 alembic 无新增 revision）
alembic current
alembic heads
# 若两者一致则直接跳过；若有 head 未应用则执行：
alembic upgrade head

# 6. 启动服务
sudo systemctl start y-sso       # 或 supervisorctl start y-sso / docker compose up -d

# 7. 健康检查
curl -sf http://127.0.0.1:8000/health
# 期望返回 {"status":"healthy",...}

# 8. 跟踪日志观察 5~10 分钟
tail -f logs/app.log
# 重点关注：SynchronousOnlyOperation / QueuePool TimeoutError / OperationalError
```

### 4.3 升级后验证清单

- [ ] `/health` 返回 200 + `status=healthy`。
- [ ] 管理员登录 → 打开用户/角色/应用管理页，数据正常。
- [ ] 任意下游系统跑一轮 OAuth2 授权码登录，拿到 `access_token` / `id_token`。
- [ ] 若启用了企微同步，检查 `/api/v1/wechat-work/sync/status` 状态正常；webhook 收到回调后响应 `success`。
- [ ] 观察 10 分钟内日志没有 `SynchronousOnlyOperation`。

### 4.4 回滚预案

**场景 A：升级后发现代码回归或异常堆栈有 `SynchronousOnlyOperation`**

1. 立即停服。
2. `git checkout <upgrade-前的-commit/tag>`。
3. `pip install -r requirements.txt`（会把 yweb 降回 0.1.3）。
4. 启动服务，`curl /health` 确认恢复。

**场景 B：不想回退业务代码、只想临时降级 yweb 行为**

可以临时把 async 检测降为警告级别，争取排查时间（**非长期方案**）：

```bash
# systemd unit 或 supervisor 配置中加入环境变量
Environment="YWEB_ASYNC_SAFETY=warn"
```

重启服务后，0.1.4 的检测会改为 `RuntimeWarning`，不再抛 500。定位问题并修复后记得移除该环境变量。

**场景 C：数据库层出现问题**

恢复 `app/db/y_sso.db.bak-<timestamp>` 备份（或用 `mysql/psql` 还原），然后按场景 A 回滚代码。

---

## 五、FAQ

### Q1：日志里突然大量出现 `SynchronousOnlyOperation: 检测到在 async 上下文中直接调用同步数据库操作！`

说明某处 `async def` 路由/中间件/依赖里漏掉了 `async_db_call()` 包装。堆栈中找到对应行号，按如下方式之一修复：

- **纯同步逻辑**：把函数改为 `def`（FastAPI 会自动放线程池）。
- **混合 async I/O**：保留 `async def`，把同步 ORM 部分抽出，用 `await async_db_call(sync_fn)` 或 `await async_db_call(lambda: User.query.filter_by(...).all())`。
- **lifespan / 启动一次性操作**：使用 `with allow_sync(): ...`（不要在请求路径中使用）。

### Q2：临时关掉检测以便紧急上线怎么办？

```bash
# 环境变量（error 抛异常 / warn 仅警告 / off 关闭）
YWEB_ASYNC_SAFETY=warn
```

请只作为应急手段，问题定位后必须还原为默认的 `error`。

### Q3：为什么 `_require_admin` / `_require_permission` 从 `async def` 改为 `def` 后反而更好？

FastAPI 对依赖函数有明确语义：

- `async def` 依赖 → 在事件循环中直接 `await`，期间任何同步 ORM 都会阻塞循环。
- `def` 依赖 → FastAPI 自动 `run_in_threadpool` 到线程池，互不干扰。

我们的权限依赖只做同步 ORM 查询，根本没有 `await` 异步 I/O，`def` 是语义更准确、性能更好的选择。

### Q4：`DynamicCORSMiddleware` 改成 `async_db_call` 后性能会不会变差？

不会。`_ensure_origins_fresh()` 在缓存命中时直接返回（`time.time()` + 比较），零开销。只有 5 分钟一次的刷新会进线程池，远小于 CORS 判断本身的开销。

### Q5：离线/内网环境如何安装 `yweb==0.1.4`？

如果服务器不能直连 PyPI，可以选择以下任意一种方式：

1. **使用内网 PyPI 镜像**（推荐）：确保镜像已同步到 0.1.4，然后
   ```bash
   pip install -r requirements.txt -i <内网镜像地址>
   ```
2. **提前下载 wheel 离线安装**：
   ```bash
   # 在有网的机器上下载
   pip download yweb==0.1.4 -d ./wheels --no-deps
   # 拷贝到目标机器后
   pip install ./wheels/yweb-0.1.4-py3-none-any.whl
   ```
3. **从 GitHub 源码构建**（备用方案，需服务器可访问 GitHub）：
   ```bash
   pip install "git+https://github.com/yafo-ai/yweb-core.git@0.1.4"
   ```

---

## 参考

- 变更检测来源：`yweb-core/yweb-core/yweb/orm/async_safety.py`
- FastAPI 异步/同步使用规范：`yweb-core/yweb-core/docs/ASYNC_SYNC_ORM_GUIDE.md`
- ORM session 管理：`yweb-core/yweb-core/docs/orm_docs/12_db_session.md`
