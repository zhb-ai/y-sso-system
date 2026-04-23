# OIDC ID Token Nonce Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `y-sso-system` 的 OIDC 授权码链路在 `scope=openid` 时返回标准 `id_token`，支持 `nonce` 透传与持久化，并在 `refresh_token` 刷新时返回新的 `id_token`。

**Architecture:** 保持现有 `Authorization Code + PKCE + JWKS + UserInfo` 结构不变，仅在 `AuthorizationCode`、`OAuth2ProviderService` 和 `oauth2` 路由上做最小补齐。`id_token` 由服务层统一构造 payload 并沿用现有 JWT 签名配置签发，避免引入第二套认证基础设施。

**Tech Stack:** FastAPI、SQLAlchemy Active Record、Alembic、yweb `JWTManager`、python-jose、pytest、TestClient

---

### Task 1: Service 层红灯测试先定义 OIDC 契约

**Files:**
- Modify: `tests/test_services/test_oauth2_provider_service.py`
- Test: `tests/test_services/test_oauth2_provider_service.py`

- [ ] **Step 1: 先为授权码换 token 写失败测试**

在 `FakeJWTManager` 上增加 `secret_key`、`algorithm` 和 `decode()` 友好能力，并新增一个最小断言：`exchange_code_for_token()` 在 `scope` 含 `openid` 时返回 `id_token`，且 `nonce` 被原样带回。

```python
def test_exchange_code_for_token_returns_id_token_and_nonce(self, monkeypatch):
    """openid 授权码换 token 时应返回带 nonce 的 id_token"""
    jwt_manager = FakeJWTManager()
    service = OAuth2ProviderService(jwt_manager=jwt_manager, user_getter=lambda _: None)

    app_obj = SimpleNamespace(
        id=100,
        name="Data Formulator",
        client_type="confidential",
        validate_is_active=Mock(),
        is_public_client=lambda: False,
    )
    service.app_service.get_application_by_client_id = Mock(return_value=app_obj)
    service.app_service.validate_client_credentials = Mock(return_value=app_obj)

    auth_code = Mock(
        application_id=100,
        user_id=7,
        redirect_uri="http://localhost:5567/callback",
        scope="openid profile email",
        nonce="nonce-123",
        code_challenge=None,
        code_challenge_method=None,
    )
    auth_code.validate_usable = Mock()
    auth_code.mark_used = Mock()

    user = SimpleNamespace(
        id=7,
        username="zhanghaibin",
        email="zhang@example.com",
        roles=[SimpleNamespace(code="admin")],
    )

    monkeypatch.setattr(AuthorizationCode, "query", QueryStub(auth_code), raising=False)
    monkeypatch.setattr(User, "query", QueryStub(user), raising=False)

    result = service.exchange_code_for_token(
        code="test-code",
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="http://localhost:5567/callback",
    )

    assert result["id_token"]
    claims = jwt.decode(
        result["id_token"],
        jwt_manager.secret_key,
        algorithms=[jwt_manager.algorithm],
        audience="client-id",
        issuer=settings.base_url.rstrip("/"),
    )
    assert claims["sub"] == "7"
    assert claims["nonce"] == "nonce-123"
    assert claims["email"] == "zhang@example.com"
```

- [ ] **Step 2: 再为 refresh 流写失败测试**

新增一个刷新场景测试，锁定两个外部契约：返回新的 `id_token`，并且 refresh 阶段不带旧 `nonce`。

```python
def test_refresh_access_token_returns_new_id_token_without_nonce(self):
    """refresh_token 刷新时应返回新的 id_token，且不复用 nonce"""
    jwt_manager = FakeJWTManager()
    refreshed_user = SimpleNamespace(
        id=7,
        username="zhanghaibin",
        email="zhang@example.com",
        is_active=True,
        roles=[SimpleNamespace(code="admin")],
    )
    service = OAuth2ProviderService(
        jwt_manager=jwt_manager,
        user_getter=lambda user_id: refreshed_user if user_id == 7 else None,
    )
    service.app_service.validate_client_credentials = Mock()

    refresh_token = jwt.encode(
        {
            "sub": "7",
            "user_id": 7,
            "token_type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(days=1),
            "iat": datetime.now(timezone.utc),
        },
        jwt_manager.secret_key,
        algorithm=jwt_manager.algorithm,
    )

    result = service.refresh_access_token(
        refresh_token=refresh_token,
        client_id="client-id",
        client_secret="client-secret",
    )

    assert result["id_token"]
    claims = jwt.decode(
        result["id_token"],
        jwt_manager.secret_key,
        algorithms=[jwt_manager.algorithm],
        audience="client-id",
        issuer=settings.base_url.rstrip("/"),
    )
    assert claims["sub"] == "7"
    assert "nonce" not in claims
```

- [ ] **Step 3: 跑定点测试，确认红灯原因是缺少新行为**

Run:

```bash
pytest tests/test_services/test_oauth2_provider_service.py::TestOAuth2ProviderService::test_exchange_code_for_token_returns_id_token_and_nonce tests/test_services/test_oauth2_provider_service.py::TestOAuth2ProviderService::test_refresh_access_token_returns_new_id_token_without_nonce -v
```

Expected:

```text
FAIL ... KeyError: 'id_token'
or
FAIL ... assert 'nonce' in claims
```

- [ ] **Step 4: 再补一个最小实体测试，锁定 nonce 会被保存**

在同一个测试文件中直接验证 `AuthorizationCode.create_code()` 会保存 `nonce`，避免后续只在 mock 对象上“自证”。

```python
def test_authorization_code_create_code_persists_nonce(self):
    """创建授权码时应保存 nonce"""
    auth_code = AuthorizationCode.create_code(
        application_id=1,
        user_id=2,
        redirect_uri="http://localhost:5567/callback",
        scope="openid profile",
        state="state-1",
        nonce="nonce-123",
        code_challenge="challenge",
        code_challenge_method="S256",
    )

    assert auth_code.nonce == "nonce-123"
```

- [ ] **Step 5: 跑 service 文件，确认新增测试先红后留在可实现范围内**

Run:

```bash
pytest tests/test_services/test_oauth2_provider_service.py -v
```

Expected:

```text
仅新增的 nonce/id_token 用例失败，现有 PKCE/sub 测试继续通过
```

### Task 2: API 层红灯测试锁定 nonce 透传与 token 响应

**Files:**
- Create: `tests/test_api/test_oauth2_provider_api.py`
- Test: `tests/test_api/test_oauth2_provider_api.py`

- [ ] **Step 1: 为 GET /authorize 的 nonce 透传写失败测试**

创建新的 API 测试文件，用 `FastAPI + create_oauth2_provider_router()` 和桩 service 组装最小应用。先锁定未登录重定向时 `nonce` 会继续出现在前端登录 URL 上。

```python
def test_authorize_redirect_preserves_nonce(client, oauth2_service_stub):
    """未登录授权跳转时应透传 nonce 到前端登录页"""
    response = client.get(
        "/api/v1/oauth2/authorize",
        params={
            "response_type": "code",
            "client_id": "client-id",
            "redirect_uri": "http://localhost:5567/callback",
            "scope": "openid profile",
            "state": "state-1",
            "nonce": "nonce-123",
            "code_challenge": "challenge",
            "code_challenge_method": "S256",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "nonce=nonce-123" in response.headers["location"]
```

- [ ] **Step 2: 为 POST /authorize 的 nonce 透传写失败测试**

同文件新增已登录授权确认测试，断言路由会把 `nonce` 传给 service 层的 `create_authorization_code()`。

```python
def test_authorize_confirm_passes_nonce_to_service(client, oauth2_service_stub):
    """授权确认时应把 nonce 传给 service"""
    response = client.post(
        "/api/v1/oauth2/authorize",
        json={
            "client_id": "client-id",
            "redirect_uri": "http://localhost:5567/callback",
            "scope": "openid profile",
            "state": "state-1",
            "nonce": "nonce-123",
            "code_challenge": "challenge",
            "code_challenge_method": "S256",
        },
    )

    assert response.status_code == 200
    oauth2_service_stub.create_authorization_code.assert_called_once_with(
        application_id=100,
        user_id=7,
        redirect_uri="http://localhost:5567/callback",
        scope="openid profile",
        state="state-1",
        nonce="nonce-123",
        code_challenge="challenge",
        code_challenge_method="S256",
    )
```

- [ ] **Step 3: 为 /token 响应带 id_token 写失败测试**

在同一个 API 文件中增加 token 路由契约测试，防止只修 service 不修 HTTP 层。

```python
def test_token_endpoint_returns_id_token(client, oauth2_service_stub):
    """token 端点应把 service 返回的 id_token 直接返回给客户端"""
    oauth2_service_stub.exchange_code_for_token.return_value = {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "id_token": "id-token",
        "token_type": "bearer",
        "expires_in": 1800,
        "scope": "openid profile",
    }

    response = client.post(
        "/api/v1/oauth2/token",
        data={
            "grant_type": "authorization_code",
            "code": "code-1",
            "redirect_uri": "http://localhost:5567/callback",
            "client_id": "client-id",
            "client_secret": "client-secret",
        },
    )

    assert response.status_code == 200
    assert response.json()["id_token"] == "id-token"
```

- [ ] **Step 4: 跑 API 定点测试，确认失败点落在 nonce 未透传**

Run:

```bash
pytest tests/test_api/test_oauth2_provider_api.py -v
```

Expected:

```text
FAIL ... assert "nonce=nonce-123" in location
or
FAIL ... expected call not found
```

### Task 3: 最小实现 nonce 持久化、id_token 签发与 refresh 返回

**Files:**
- Modify: `app/domain/application/entities.py`
- Modify: `app/domain/application/services.py`
- Modify: `app/api/v1/oauth2.py`
- Create: `alembic/versions/6c1d8e4a7b21_add_nonce_to_authorization_code.py`

- [ ] **Step 1: 在实体与迁移里补齐 nonce 持久化**

先改模型，再补 Alembic，保证数据库与 ORM 一致。`AuthorizationCode` 增加可空 `nonce` 字段，`create_code()` 接收并保存它。

```python
nonce: Mapped[Optional[str]] = mapped_column(
    String(255), nullable=True, comment="OIDC nonce 参数"
)

@classmethod
def create_code(
    cls,
    application_id: int,
    user_id: int,
    redirect_uri: str,
    scope: str = None,
    state: str = None,
    nonce: str = None,
    code_challenge: str = None,
    code_challenge_method: str = None,
    expires_minutes: int = 5,
) -> "AuthorizationCode":
    auth_code = cls()
    auth_code.nonce = nonce
```

迁移脚本保持可回滚、可空：

```python
def upgrade() -> None:
    with op.batch_alter_table("authorization_code", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("nonce", sa.String(length=255), nullable=True, comment="OIDC nonce 参数")
        )

def downgrade() -> None:
    with op.batch_alter_table("authorization_code", schema=None) as batch_op:
        batch_op.drop_column("nonce")
```

- [ ] **Step 2: 在 API 层保持瘦路由，只做参数透传**

给 `AuthorizeConfirmRequest` 增加 `nonce` 字段；`GET /authorize` 和 `POST /authorize` 只负责收参并把 `nonce` 传给 service，不做业务判断。

```python
class AuthorizeConfirmRequest(BaseModel):
    client_id: str
    redirect_uri: str
    scope: Optional[str] = None
    state: Optional[str] = None
    nonce: Optional[str] = None
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None

def authorize(..., nonce: str = Query(None, description="OIDC nonce 参数"), ...):
    ...
    if nonce:
        login_params["nonce"] = nonce
    ...
    auth_code = oauth2_provider_service.create_authorization_code(
        ...,
        nonce=nonce,
        ...
    )
```

- [ ] **Step 3: 在 Service 层统一组装 TokenPayload 与 id_token claims**

不要在 API 层拼 claims。把用户查询、`iss/aud`、`sub` 一致性和 `nonce` 处理收口到 service 内部辅助函数。

```python
def _build_token_payload(self, user, client_id: str) -> TokenPayload:
    roles = [r.code if hasattr(r, "code") else str(r) for r in getattr(user, "roles", [])]
    return TokenPayload(
        sub=str(user.id),
        user_id=user.id,
        username=user.username,
        email=getattr(user, "email", None),
        roles=roles,
        extra={
            "iss": settings.base_url.rstrip("/"),
            "aud": client_id,
        },
    )

def _create_id_token(self, user, client_id: str, nonce: Optional[str] = None) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(user.id),
        "iss": settings.base_url.rstrip("/"),
        "aud": client_id,
        "iat": now,
        "exp": now + timedelta(minutes=self.jwt_manager.access_token_expire_minutes),
        "name": getattr(user, "name", None) or user.username,
        "email": getattr(user, "email", None),
        "preferred_username": user.username,
    }
    if nonce:
        claims["nonce"] = nonce
    return jwt.encode(claims, self.jwt_manager.secret_key, algorithm=self.jwt_manager.algorithm)
```

- [ ] **Step 4: 把 authorization_code 与 refresh_token 两条返回路径补绿**

在 `exchange_code_for_token()` 中只在 `scope` 含 `openid` 时返回 `id_token`；在 `refresh_access_token()` 中根据 refresh token 找到用户后补签一个新的 `id_token`，但不带 `nonce`。

```python
payload = self._build_token_payload(user, client_id)
access_token = self.jwt_manager.create_access_token(payload)
refresh_token = self.jwt_manager.create_refresh_token(payload)

response = {
    "access_token": access_token,
    "token_type": "bearer",
    "expires_in": self.jwt_manager.access_token_expire_minutes * 60,
    "refresh_token": refresh_token,
    "scope": auth_code.scope or "",
}
if "openid" in (auth_code.scope or "").split():
    response["id_token"] = self._create_id_token(user, client_id, nonce=getattr(auth_code, "nonce", None))
```

refresh 路径补成：

```python
token_data = self.jwt_manager.verify_token(refresh_token)
if not token_data or token_data.token_type != "refresh" or not token_data.user_id:
    raise ValueError("refresh_token 无效或已过期")

user = self.user_getter(token_data.user_id)
if not user or (hasattr(user, "is_active") and not user.is_active):
    raise ValueError("refresh_token 无效或已过期")

response["id_token"] = self._create_id_token(user, client_id)
```

- [ ] **Step 5: 跑前两轮测试，确认转绿**

Run:

```bash
pytest tests/test_services/test_oauth2_provider_service.py tests/test_api/test_oauth2_provider_api.py -v
```

Expected:

```text
all selected tests passed
```

### Task 4: 全量回归与本地联调验证

**Files:**
- Modify: `tests/test_services/test_oauth2_provider_service.py`
- Modify: `tests/test_api/test_oauth2_provider_api.py`
- Modify: `app/domain/application/services.py`

- [ ] **Step 1: 补一个 refresh 续期场景回归，防止丢失 refresh_token**

确保当 `JWTManager.refresh_tokens()` 触发滑动续期时，响应里同时保留新的 `refresh_token` 和新的 `id_token`。

```python
assert response["access_token"]
assert response["id_token"]
assert response["refresh_token"] == "new-refresh-token"
```

- [ ] **Step 2: 跑目标测试集，确保旧行为未回退**

Run:

```bash
pytest tests/test_services/test_oauth2_provider_service.py tests/test_api/test_oidc_discovery.py tests/test_api/test_settings_oauth2_endpoints.py tests/test_api/test_oauth2_provider_api.py -v
```

Expected:

```text
现有 PKCE、sub 一致性、Discovery/JWKS 测试继续通过
```

- [ ] **Step 3: 运行数据库迁移与服务级 smoke test**

Run:

```bash
alembic upgrade head
pytest tests/test_services/test_oauth2_provider_service.py -v
```

Expected:

```text
迁移执行成功，service 测试全部通过
```

- [ ] **Step 4: 最终本地联调验证**

Run:

```bash
python dev_server.py
```

然后验证：

```text
1. 浏览器走一次 Data Formulator 的 OIDC 登录
2. /api/v1/oauth2/token 的 JSON 中包含 id_token
3. refresh_token 刷新响应中包含新的 id_token
4. 首次登录的 id_token 带 nonce，refresh 后的新 id_token 不带 nonce
```
