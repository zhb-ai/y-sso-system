# SSO 系统问题分析与改进方案

> **文档类型**：分析文档（仅分析，不含实际代码改动）
>
> **分析日期**：2026-04-12
>
> **涉及问题**：
> 1. 缺少标准 OIDC Discovery 端点（§3.1）
> 2. `sub` claim 在 JWT 和 UserInfo 之间不一致（§7.1）
> 3. JWKS 公钥端点缺失（§3.2）
> 4. issuer 使用 localhost 而非外部地址（§3.3）
> 5. 不支持 PKCE / 无公开客户端支持（§3.4）
> 6. UserInfo 响应 email 为 null（§7.2）
> 7. 管理后台缺少第三方对接配置面板（§五）

---

## 一、问题 1：缺少标准 OIDC Discovery 端点

### 1.1 现状分析

**结论：问题确认存在。**

当前系统实现了一个 RFC 8414 授权服务器元数据端点，但存在两个问题：

| 项目 | 期望（OIDC 标准） | 实际 |
|------|-------------------|------|
| 端点路径 | `GET /.well-known/openid-configuration` | `GET /api/v1/oauth2/.well-known/oauth-authorization-server` |
| 端点位置 | 挂载在应用根路径 | 嵌套在 OAuth2 子路由下 |
| 返回字段 | 包含 `jwks_uri`、`id_token_signing_alg_values_supported` 等 OIDC 字段 | 仅包含基础 OAuth2 字段 |

**现有元数据端点代码**（`app/api/v1/oauth2.py` 第 340-367 行）：

```python
@router.get(
    "/.well-known/oauth-authorization-server",
    summary="OAuth2 授权服务器元数据",
)
def authorization_server_metadata(request: Request):
    base_url = str(request.base_url).rstrip("/")
    prefix = "/api/v1/oauth2"
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}{prefix}/authorize",
        "token_endpoint": f"{base_url}{prefix}/token",
        "userinfo_endpoint": f"{base_url}{prefix}/userinfo",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
        "scopes_supported": ["openid", "profile", "email"],
        "subject_types_supported": ["public"],
    }
```

**缺失的 OIDC 标准字段**：

- `jwks_uri` — 公钥端点
- `id_token_signing_alg_values_supported` — ID Token 签名算法
- `code_challenge_methods_supported` — PKCE 支持声明

**路径问题**：由于 `router = APIRouter(prefix="/oauth2")`，且在 `routes.py` 中以 `prefix="/api/v1"` 挂载，实际访问路径为 `/api/v1/oauth2/.well-known/oauth-authorization-server`，而非 OIDC 标准要求的根路径 `/.well-known/openid-configuration`。

### 1.2 影响范围

1. **所有标准 OIDC 客户端**无法自动发现端点，必须手动配置 `authorize_url`、`token_url`、`userinfo_url`
2. **Data Formulator 等对接方**需要配置 7 个环境变量（模式 B），而非 2-3 个（模式 A）
3. 对接沟通成本高，每个新应用接入都需要人工告知各端点地址

### 1.3 改进方案

#### 方案概述

需要做两件事：

1. **在应用根路径添加 OIDC Discovery 端点** — 新增 `GET /.well-known/openid-configuration`
2. **保留现有 RFC 8414 端点** — 兼容已有的集成

#### 方案 A：在 `main.py` 中直接注册根路径端点（推荐）

在 `app/main.py` 中直接注册一个根级别路由，无需修改现有 OAuth2 路由模块。

**需要添加的路由**：

```
GET /.well-known/openid-configuration
```

**返回 JSON 内容**：

```json
{
  "issuer": "{base_url}",
  "authorization_endpoint": "{base_url}/api/v1/oauth2/authorize",
  "token_endpoint": "{base_url}/api/v1/oauth2/token",
  "userinfo_endpoint": "{base_url}/api/v1/oauth2/userinfo",
  "jwks_uri": "{base_url}/api/v1/oauth2/jwks",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "subject_types_supported": ["public"],
  "id_token_signing_alg_values_supported": ["HS256"],
  "scopes_supported": ["openid", "profile", "email"],
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
  "code_challenge_methods_supported": ["S256"]
}
```

**关键细节**：

- `issuer` 应从 `settings.base_url`（即 `config/settings.yaml` 中的 `base_url`）获取，**不能**用 `request.base_url`（因为反向代理后 request.base_url 可能是内网地址如 `http://localhost:8000`）
- 此路由必须在 `main.py` 的 catch-all 前端路由 `/{full_path:path}` **之前**注册，否则会被前端路由拦截
- 当前 `settings.yaml_demo` 中 `base_url` 为 `http://localhost:8000`，生产环境需改为 `https://sso.haocai.com.cn:8080`

**注册位置**：在 `main.py` 的"基础端点"区域（`/health` 旁边），或在 `routes.py` 中将其作为一个独立路由直接挂载到 `app`。

#### 方案 B：在 OAuth2 路由模块中添加，由 `routes.py` 以根前缀挂载

在 `app/api/v1/oauth2.py` 的 `create_oauth2_provider_router` 函数中增加一个独立路由，但让 `routes.py` 将其以 `prefix=""` 挂载到根路径。

此方案耦合度较高，不推荐。

#### issuer 的来源问题

当前元数据端点使用 `request.base_url` 作为 `issuer`，这在反向代理环境下会返回内网地址。改进方案：

| 方式 | 来源 | 适用场景 |
|------|------|---------|
| 当前 | `request.base_url` | 仅适用于直连（无反向代理） |
| **推荐** | `settings.base_url`（YAML 配置） | 适用于所有场景，管理员可控 |

需要同时修改现有的 RFC 8414 元数据端点，将 `issuer` 也改为从配置获取。

#### 实施步骤

1. 在 `main.py`（或 `routes.py`）添加 `GET /.well-known/openid-configuration` 路由
2. 路由返回标准 OIDC Discovery JSON，`issuer` 和各端点 URL 基于 `settings.base_url`
3. 确保该路由在 catch-all `/{full_path:path}` 之前注册
4. 修改现有 RFC 8414 端点的 `issuer` 来源为 `settings.base_url`
5. 生产环境 `settings.yaml` 中配置正确的 `base_url: "https://sso.haocai.com.cn:8080"`

---

## 二、问题 2：`sub` claim 在 JWT 和 UserInfo 之间不一致

### 2.1 现状分析

**结论：Bug 确认存在。**

代码中 `sub` 的赋值逻辑在两个不同位置使用了不同的值：

**JWT Token 中的 `sub`**（`app/domain/application/services.py` 第 452 行）：

```python
payload = TokenPayload(
    sub=user.username,       # ← 用户名，如 "zhanghaibin"
    user_id=user.id,
    username=user.username,
    email=getattr(user, 'email', None),
    roles=roles,
)
```

**UserInfo 端点中的 `sub`**（`app/domain/application/services.py` 第 536-537 行）：

```python
userinfo = {
    "sub": str(user.id),     # ← 数据库 ID，如 "7"
    "preferred_username": user.username,
    ...
}
```

| 来源 | 代码位置 | `sub` 值 | 实际含义 |
|------|---------|----------|---------|
| JWT Access Token | `exchange_code_for_token` 第 452 行 | `user.username`（如 `"zhanghaibin"`） | 用户登录名 |
| UserInfo 响应 | `get_userinfo` 第 537 行 | `str(user.id)`（如 `"7"`） | 数据库自增 ID |

### 2.2 违反的规范

根据 [OpenID Connect Core 1.0 §5.3](https://openid.net/specs/openid-connect-core-1_0.html#UserInfoResponse)：

> The `sub` Claim in the UserInfo Response MUST be verified to exactly match the `sub` Claim in the ID Token; if they do not match, the UserInfo Response values MUST NOT be used.

虽然当前系统签发的是 Access Token 而非 ID Token，但作为 OIDC 兼容的 OAuth2 Provider，`sub` 在所有上下文中保持一致是基本要求。任何遵循标准的 OIDC 客户端在发现 `sub` 不一致时都可能拒绝使用 UserInfo 数据。

### 2.3 实际影响

1. **身份混乱**：使用 JWKS 本地验证的客户端（解析 JWT）识别用户为 `"zhanghaibin"`，使用 UserInfo 验证的客户端识别用户为 `"7"`，同一用户被视为两个不同的人
2. **数据隔离错误**：Data Formulator 根据 `sub` 创建用户工作空间，两种验证模式会产生不同的目录路径
3. **迁移风险**：如果客户端先用 UserInfo 模式（`sub="7"`）创建了数据，后切换为 JWKS 模式（`sub="zhanghaibin"`），原有数据将不可访问

### 2.4 改进方案

#### 核心原则

**`sub` 必须在 JWT 和 UserInfo 中使用相同的值。** 无论选择哪个值作为 `sub`，都必须统一。

#### 方案对比

| 方案 | `sub` 统一为 | 需要改动的位置 | 优点 | 缺点 |
|------|-------------|--------------|------|------|
| **A（推荐）** | `str(user.id)` | `exchange_code_for_token` 中的 `TokenPayload.sub` | 不可变、唯一、与数据库主键对应 | 可读性差，调试时不直观 |
| B | `user.username` | `get_userinfo` 中的 `"sub"` | 可读性好 | 用户名可改，改后会破坏所有历史关联 |
| C | UUID（新增字段） | 两处都改 + User 模型加字段 + 数据迁移 | 最佳实践，不可变且无信息泄漏 | 改动量大，需数据库迁移 |

#### 推荐方案 A 详解：统一为 `str(user.id)`

**理由**：

- 数据库主键是天然的不可变唯一标识
- `user.id` 已经在 `TokenPayload` 的 `user_id` 字段中存在，只需将 `sub` 也改为它
- 不需要数据库迁移
- UserInfo 端点无需改动（已经是 `str(user.id)`）

**需要修改的代码**（仅 1 处）：

文件：`app/domain/application/services.py`，第 452 行

```python
# 改动前
payload = TokenPayload(
    sub=user.username,          # ← 不一致的根源
    user_id=user.id,
    username=user.username,
    ...
)

# 改动后
payload = TokenPayload(
    sub=str(user.id),           # ← 统一为用户 ID
    user_id=user.id,
    username=user.username,
    ...
)
```

**同时建议**在 UserInfo 响应中确保包含足够的用户信息字段，让客户端不需要依赖 `sub` 的可读性：

```python
userinfo = {
    "sub": str(user.id),                     # 唯一标识（与 JWT 一致）
    "preferred_username": user.username,       # 登录名
    "name": getattr(user, 'display_name', user.username),  # 显示名
    "email": getattr(user, 'email', None),
    ...
}
```

#### 兼容性影响评估

修改 JWT 中的 `sub` 后，需要评估以下影响：

| 影响范围 | 影响程度 | 说明 |
|---------|---------|------|
| SSO 系统内部（本系统） | **无影响** | 内部认证使用 `user_id` 字段，不依赖 `sub` |
| Data Formulator | **需配合切换** | 如果之前使用 `OIDC_IDENTITY_CLAIM=preferred_username` 绕过了此 Bug，修复后可移除该配置 |
| 已有的其他对接方 | **需逐一确认** | 如果有客户端缓存了旧 JWT 的 `sub`（username），需在 token 过期后重新登录 |
| `yweb` 框架内部 | **需确认** | 需检查 `JWTManager.verify_token` 是否依赖 `sub` 做任何逻辑判断 |

#### 实施步骤

1. **确认框架影响**：检查 `yweb` 的 `JWTManager` 和 `TokenPayload` 中是否有对 `sub` 做特殊处理的逻辑
2. **修改代码**：将 `exchange_code_for_token` 中 `TokenPayload` 的 `sub` 改为 `str(user.id)`
3. **通知对接方**：告知所有已对接的客户端，`sub` 将从用户名变为用户 ID
4. **对接方配合**：Data Formulator 移除 `OIDC_IDENTITY_CLAIM=preferred_username` 配置
5. **验证**：发起新的 OAuth2 授权流程，对比 JWT 解码后的 `sub` 与 UserInfo 返回的 `sub` 是否一致

---

## 三、问题 3：JWKS 公钥端点缺失

### 3.1 现状分析

**结论：问题确认存在。**

在整个 `app/` 目录中搜索 `jwks`、`JWK`、`public_key`、`RSA` 等关键词，**结果为零**。系统完全没有实现 JWKS 端点。

同时，JWT 签名使用的是 **HS256**（对称密钥）：

```yaml
# config/settings.yaml_demo
jwt:
  secret_key: "your-secret-key-change-this-in-production"
  algorithm: HS256
```

HS256 使用共享密钥签名，第三方客户端**无法**在本地验证 JWT 签名（因为不能把 secret_key 分发给客户端），只能通过调用 UserInfo 端点来间接验证 token 有效性。

### 3.2 影响

1. **性能瓶颈**：每次 API 请求都需要回调 SSO 的 UserInfo 端点验证 token，在高并发场景下 SSO 成为瓶颈
2. **无法离线验证**：SSO 不可用时，所有依赖 SSO token 的下游系统全部失败
3. **不符合 OIDC 标准**：标准 OIDC Provider 应提供 JWKS 端点供客户端获取公钥

### 3.3 改进方案

此问题涉及面较广，建议分两步走：

**第一步（短期）**：先添加一个 JWKS 端点，返回当前 HS256 密钥的公开信息（但 HS256 的密钥本身不能公开，所以实际上只能声明端点存在）。实际意义有限。

**第二步（中期，推荐）**：将 JWT 签名算法从 **HS256 改为 RS256**（非对称密钥）。

| 项目 | HS256（当前） | RS256（目标） |
|------|-------------|-------------|
| 密钥类型 | 共享密钥 | RSA 公私钥对 |
| 签名方 | SSO 用 secret_key 签名 | SSO 用私钥签名 |
| 验证方 | 需要知道 secret_key | 只需公钥（可公开） |
| JWKS 端点 | 无意义（不能公开密钥） | **有意义**（公开公钥） |
| 客户端本地验证 | 不可能 | **可以** |

**改动范围**：

1. 生成 RSA 密钥对，私钥存储在服务端配置中
2. 修改 `settings.yaml` 中 `jwt.algorithm` 为 `RS256`，添加 `private_key_path` / `public_key_path`
3. 依赖 `yweb` 框架的 `JWTManager` 是否支持 RS256（需确认）
4. 添加 `GET /api/v1/oauth2/jwks` 端点，返回 RSA 公钥的 JWK 格式
5. Discovery 端点中的 `jwks_uri` 指向此端点

---

## 四、问题 4：issuer 使用 localhost 而非外部地址

### 4.1 现状分析

**结论：问题确认存在。存在两个层面的问题。**

**层面 1：配置默认值为 localhost**

`app/config.py` 第 21 行：

```python
class Settings(AppSettings):
    base_url: str = Field(default="http://localhost:8000", description="应用基础URL")
```

`config/settings.yaml_demo` 第 74 行：

```yaml
base_url: "http://localhost:8000"
```

生产环境的 `settings.yaml` 中如果未修改，`base_url` 将是 `http://localhost:8000`，导致 JWT 中的 `iss` claim 为内网地址。

**层面 2：元数据端点使用 `request.base_url` 而非配置**

`app/api/v1/oauth2.py` 第 348 行：

```python
def authorization_server_metadata(request: Request):
    base_url = str(request.base_url).rstrip("/")  # ← 来自请求，非配置
    ...
    return {"issuer": base_url, ...}
```

在反向代理（Nginx → SSO）场景下，`request.base_url` 返回的是 Nginx 到 SSO 的内网地址（如 `http://127.0.0.1:8000`），而非用户实际访问的外网地址 `https://sso.haocai.com.cn:8080`。

### 4.2 影响

1. **JWT 的 `iss` claim 为 localhost**：任何做 issuer 校验的客户端（标准 OIDC 客户端都会做）将拒绝此 token
2. **Discovery 返回的 issuer 与实际不符**：客户端自动发现后，issuer 校验失败
3. **如果未来启用 JWKS 本地验证**：客户端要求 `iss == issuer`，不一致会直接导致验证失败

### 4.3 改进方案

1. **修改元数据端点**：将 `issuer` 来源从 `request.base_url` 改为 `settings.base_url`
2. **确保生产 `settings.yaml`** 中 `base_url` 为实际外部地址 `https://sso.haocai.com.cn:8080`
3. **确认 `yweb` 框架**的 `JWTManager` 在生成 JWT 时 `iss` claim 的来源（可能也需要传入 `base_url`）

---

## 五、问题 5：不支持 PKCE / 无公开客户端支持

### 5.1 现状分析

**结论：问题确认存在。**

在整个代码库中搜索 `code_challenge`、`code_verifier`、`pkce`、`PKCE`，**结果为零**（仅出现在本分析文档中）。

当前 token 端点**强制要求** `client_secret`（`app/api/v1/oauth2.py` 第 233 行）：

```python
if not client_id or not client_secret:
    return JSONResponse(
        status_code=401,
        content={"error": "invalid_client", "error_description": "缺少客户端凭证"},
    )
```

同时，`AuthorizationCode` 实体（`app/domain/application/entities.py`）没有 `code_challenge` 和 `code_challenge_method` 字段：

```python
class AuthorizationCode(BaseModel):
    code: ...
    application = ...
    user = ...
    redirect_uri: ...
    scope: ...
    state: ...
    expires_at: ...
    is_used: ...
    # ← 无 code_challenge / code_challenge_method 字段
```

### 5.2 影响

1. **安全风险**：Data Formulator 是浏览器 SPA 应用，`client_secret` 在前端 JavaScript 中完全可见，任何人都可以提取并冒充该客户端
2. **不符合 OAuth 2.1 草案**：OAuth 2.1 要求所有客户端使用 PKCE
3. **无法注册公开客户端**：`Application` 模型的 `client_secret` 为 `nullable=False`，不允许无密钥的客户端

### 5.3 改进方案

**涉及 3 个层面的改动**：

**5.3.1 数据库层**：`AuthorizationCode` 模型添加字段

```
code_challenge: Optional[str]        — PKCE code_challenge
code_challenge_method: Optional[str] — "S256" 或 "plain"
```

**5.3.2 authorize 端点**：接受 `code_challenge` 和 `code_challenge_method` 参数

```
GET /api/v1/oauth2/authorize?...&code_challenge=xxx&code_challenge_method=S256
```

将 `code_challenge` 存入 `AuthorizationCode` 记录。

**5.3.3 token 端点**：支持 `code_verifier` 替代 `client_secret`

当授权码关联了 `code_challenge` 时：
- 接受 `code_verifier` 参数
- 计算 `BASE64URL(SHA256(code_verifier))` 并与存储的 `code_challenge` 比较
- 匹配则通过，**不要求 `client_secret`**

当授权码**没有** `code_challenge` 时（传统机密客户端流程）：
- 保持现有行为，要求 `client_secret`

**5.3.4 Application 模型（可选）**：支持公开客户端类型

在 `Application` 模型中添加 `client_type` 字段（`confidential` / `public`），公开客户端允许 `client_secret` 为空。

---

## 六、问题 6：UserInfo 响应 email 为 null

### 6.1 现状分析

**结论：此问题是数据问题，非代码 Bug。**

UserInfo 端点的代码逻辑是正确的（`app/domain/application/services.py` 第 540 行）：

```python
"email": getattr(user, 'email', None),
```

`User` 模型继承自 `AbstractUser`，其中包含 `email` 字段。问题在于：

- 用户记录的 `email` 字段本身为 `NULL`（未填写）
- 或者用户通过企业微信等渠道创建，同步时未带入邮箱信息

### 6.2 影响

影响较小。email 在 OIDC 中不是必填字段。但对于 Data Formulator 等需要用邮箱展示用户信息的系统，会导致界面显示不完整。

### 6.3 改进方案

此问题不需要代码改动。建议：

1. **管理员操作**：在 SSO 管理后台为用户补充 email 信息
2. **企业微信同步时**：确认同步逻辑是否提取了企业微信中的邮箱字段并写入 User 记录
3. **UserInfo 响应优化（可选）**：当 email 为 null 时，可以尝试从关联的员工信息中获取邮箱作为 fallback

---

## 七、问题 7：管理后台缺少第三方对接配置面板

### 7.1 现状分析

**结论：问题确认存在。**

当前应用管理页面（`frontend/src/pages/applications/Index.vue`）的功能：

| 已有功能 | 缺失功能 |
|---------|---------|
| 应用列表（名称、编码、状态） | Issuer URL |
| 客户端 ID（可复制） | Discovery URL |
| 创建/编辑/删除应用 | Authorization Endpoint |
| 重置密钥（弹窗显示 client_id + client_secret） | Token Endpoint |
| 启用/禁用切换 | UserInfo Endpoint |
| | JWKS URI |
| | 支持的 Grant Types |
| | 支持的 Scopes |
| | 是否支持 PKCE |

现有的"客户端凭证"弹窗（第 224-261 行）仅展示 `client_id` 和 `client_secret`，缺少所有 OAuth2 端点地址。第三方系统对接时，无法从管理界面获取配置参数，必须额外沟通。

### 7.2 改进方案

**在应用列表页的操作列或应用编辑弹窗中，增加一个"对接配置"按钮/面板**，展示该应用对接所需的全部信息。

需要的信息来源：

| 信息 | 来源 | 说明 |
|------|------|------|
| Issuer URL | `settings.base_url`（后端 API 返回） | 需要新增一个 API 或在应用详情 API 中附带 |
| Discovery URL | `{issuer}/.well-known/openid-configuration` | 前端拼接 |
| Authorization Endpoint | `{issuer}/api/v1/oauth2/authorize` | 前端拼接 |
| Token Endpoint | `{issuer}/api/v1/oauth2/token` | 前端拼接 |
| UserInfo Endpoint | `{issuer}/api/v1/oauth2/userinfo` | 前端拼接 |
| JWKS URI | `{issuer}/api/v1/oauth2/jwks` | 前端拼接 |
| 客户端 ID | 应用记录的 `client_id` | 已有 |
| 客户端密钥 | 应用记录的 `client_secret` | 已有（但仅重置时显示） |

**实现方式**：

1. **后端**：新增 `GET /api/v1/settings/oauth2-endpoints` API 或在现有的系统设置 API 中返回 `base_url` + 端点路径模板
2. **前端**：在应用列表的操作列增加"对接配置"按钮，弹出对话框展示所有配置项，每项带"复制"按钮，以及"复制全部"按钮

---

## 八、全量总结

| # | 问题 | 是否存在 | 类型 | 严重程度 | 改动量 | 优先级 |
|---|------|---------|------|---------|--------|--------|
| 1 | OIDC Discovery 端点缺失 | **是** | 功能缺失 | 中 | 低（1 个路由） | 推荐 |
| 2 | **`sub` claim JWT/UserInfo 不一致** | **是** | **Bug** | **高** | **极低（1 行）** | **最高** |
| 3 | JWKS 公钥端点缺失 | **是** | 功能缺失 | 中 | 中（需改签名算法） | 中期 |
| 4 | issuer 为 localhost | **是** | 配置/设计问题 | **高** | 低（改配置+代码） | **高** |
| 5 | 不支持 PKCE | **是** | 安全缺陷 | 中高 | 中（3 层改动） | 推荐 |
| 6 | UserInfo email 为 null | **是** | 数据问题 | 低 | 无代码改动 | 低 |
| 7 | 管理后台缺少对接配置面板 | **是** | 功能缺失 | 低 | 中（前端+后端） | 推荐 |

### 建议实施顺序

```
第一批（立即）：
  ├── #2 修复 sub 一致性           ← 1 行代码，消除 OIDC 规范违反
  └── #4 修复 issuer 来源          ← 改配置 + 元数据端点 issuer 来源

第二批（短期）：
  ├── #1 添加 Discovery 端点       ← 1 个新路由
  └── #7 管理后台对接配置面板       ← 前端 UI 增强

第三批（中期）：
  ├── #5 实现 PKCE 支持            ← 安全性提升
  └── #3 JWT 改为 RS256 + JWKS 端点 ← 性能提升，支持本地验证

持续：
  └── #6 补充用户 email 数据        ← 管理员操作
```
