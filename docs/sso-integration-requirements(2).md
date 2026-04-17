# SSO 系统对接 Data Formulator — 需求说明

> 本文档用于与 SSO 系统管理员沟通，说明 Data Formulator 对接 SSO 所需的接口和配置。

---

## 一、背景

Data Formulator 需要接入公司 SSO 系统实现单点登录。Data Formulator 前端是一个浏览器单页应用（SPA），使用标准的 **OAuth2 Authorization Code** 流程进行认证。

Data Formulator 支持两种对接模式：

| 模式 | 适用场景 | SSO 侧工作量 |
|------|---------|-------------|
| **模式 A（自动发现）** | SSO 有标准 OIDC Discovery 端点 | 最小（可能只需开启配置） |
| **模式 B（手动端点）** | SSO 无 Discovery，仅有基本 OAuth2 接口 | **零**（不需要改 SSO） |

**如果 SSO 系统目前已有 authorize、token、userinfo 这三个端点**，则不需要做任何改动即可对接（模式 B）。以下是两种模式的详细说明。

---

## 二、模式 B：最低要求（无需改动 SSO）

如果 SSO 系统**已经有**以下三个 OAuth2 端点，Data Formulator 可以直接对接，**SSO 侧不需要做任何改动**：

| 端点 | 当前 SSO 地址 | 是否必须 |
|------|-------------|---------|
| 授权端点 | `https://sso.haocai.com.cn:8080/api/v1/oauth2/authorize` | **必须** |
| Token 端点 | `https://sso.haocai.com.cn:8080/api/v1/oauth2/token` | **必须** |
| UserInfo 端点 | `https://sso.haocai.com.cn:8080/api/v1/oauth2/userinfo` | **推荐** |

Data Formulator 侧的配置：

```
AUTH_PROVIDER=oidc
OIDC_ISSUER_URL=https://sso.haocai.com.cn:8080
OIDC_CLIENT_ID=nqB6VTGmZM49KvoxPqb4j-rpXHXbutAigvLsaWGY5MU
OIDC_CLIENT_SECRET=pQm_ZXUQFo3wjgQXxMOuHuB5jlWN-LLBUCuXqSnMyZOAHu5sMHQzb-Caa9pKIyXV
OIDC_AUTHORIZE_URL=https://sso.haocai.com.cn:8080/api/v1/oauth2/authorize
OIDC_TOKEN_URL=https://sso.haocai.com.cn:8080/api/v1/oauth2/token
OIDC_USERINFO_URL=https://sso.haocai.com.cn:8080/api/v1/oauth2/userinfo
```

**Token 验证方式**：后端拿到前端传来的 access_token 后，直接调用 SSO 的 UserInfo 端点验证 token 是否有效。如果 UserInfo 返回了用户信息，说明 token 有效。

**此模式下 SSO 侧不需要**：
- ❌ Discovery 端点
- ❌ JWKS 端点
- ❌ JWT 格式的 access_token
- ❌ 修改 issuer 配置

---

## 三、模式 A：完整对接（推荐，提升性能和安全性）

如果 SSO 管理员有条件做改进，以下增强可以提升性能和安全性：

### 3.1 OpenID Discovery 端点（推荐）

**路径**：`GET /api/v1/oauth2/.well-known/openid-configuration`

**好处**：Data Formulator 只需配置 2 个变量（`OIDC_ISSUER_URL` + `OIDC_CLIENT_ID`），其余端点自动获取。

**返回内容**（JSON，可以是静态响应）：

```json
{
  "issuer": "https://sso.haocai.com.cn:8080",
  "authorization_endpoint": "https://sso.haocai.com.cn:8080/api/v1/oauth2/authorize",
  "token_endpoint": "https://sso.haocai.com.cn:8080/api/v1/oauth2/token",
  "userinfo_endpoint": "https://sso.haocai.com.cn:8080/api/v1/oauth2/userinfo",
  "jwks_uri": "https://sso.haocai.com.cn:8080/api/v1/oauth2/jwks",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "subject_types_supported": ["public"],
  "id_token_signing_alg_values_supported": ["RS256"],
  "scopes_supported": ["openid", "profile", "email"],
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
  "code_challenge_methods_supported": ["S256"]
}
```

### 3.2 JWKS 公钥端点（推荐）

**路径**：建议 `GET /api/v1/oauth2/jwks`

**好处**：后端可以在本地验证 JWT 签名，无需每次请求都调用 SSO 的 UserInfo 端点，**性能提升显著**（尤其在高并发场景下）。

**返回示例**：

```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "my-key-id",
      "use": "sig",
      "alg": "RS256",
      "n": "Base64url 编码的 RSA 模数...",
      "e": "AQAB"
    }
  ]
}
```

### 3.3 issuer 与外部访问地址一致（仅 JWKS 模式需要）

**仅在启用 JWKS 本地验证时重要**。如果只用 UserInfo 验证（模式 B），此项不影响。

**当前问题**：SSO 系统内部配置的 issuer 是 `http://localhost:8000`，但实际对外地址是 `https://sso.haocai.com.cn:8080`。

**需要修改**：将 SSO 系统的 issuer 配置改为 `https://sso.haocai.com.cn:8080`，确保以下三处一致：

| 位置 | 当前值 | 需改为 |
|------|--------|--------|
| SSO 配置文件中的 issuer | `http://localhost:8000` | `https://sso.haocai.com.cn:8080` |
| Discovery JSON 中的 `"issuer"` | — | `https://sso.haocai.com.cn:8080` |
| JWT token 中的 `iss` claim | `http://localhost:8000` | `https://sso.haocai.com.cn:8080` |

### 3.4 PKCE 支持（推荐）

**当前情况**：客户端认证方式只有 `client_secret_basic` 和 `client_secret_post`。

**问题**：Data Formulator 是浏览器应用，客户端密钥（client_secret）放在前端 JavaScript 中会被用户看到，存在安全风险。

**建议**：为 OAuth2 客户端增加 **PKCE（Proof Key for Code Exchange, [RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636)）** 支持，允许客户端在不传 `client_secret` 的情况下完成授权码交换。

具体来说：
- 授权请求时接受 `code_challenge` 和 `code_challenge_method=S256` 参数
- Token 请求时接受 `code_verifier` 参数代替 `client_secret`
- 允许注册"公开客户端"（public client），即不要求 client_secret

> 目前 Data Formulator 已支持 `client_secret` 方式对接，可以先跑通测试，生产环境建议切换为 PKCE。

### 3.5 JWT Access Token 的 claim 要求（仅 JWKS 模式）

**仅在启用 JWKS 本地验证时需要**。如果只用 UserInfo 验证（模式 B），后端从 UserInfo 响应中获取用户信息，不解析 JWT。

| Claim | 说明 | 是否必须 |
|-------|------|---------|
| `sub` | 用户唯一标识（用户 ID） | **必须** |
| `iss` | 签发者，必须等于 `https://sso.haocai.com.cn:8080` | **必须** |
| `aud` | 受众，必须包含客户端 ID | **必须** |
| `exp` | 过期时间（Unix 时间戳） | **必须** |
| `name` | 用户显示名称 | 推荐 |
| `email` | 用户邮箱 | 推荐 |

---

## 四、Data Formulator 的客户端注册信息

在 SSO 系统中为 Data Formulator 注册应用时需要配置：

| 配置项 | 值 |
|--------|-----|
| 客户端类型 | 建议：公开客户端（Public Client）+ PKCE；当前：机密客户端 |
| 授权类型 | `authorization_code`, `refresh_token` |
| 重定向 URI | `http://localhost:5567/callback`（开发环境） |
| Scopes | `profile email`（模式 B）或 `openid profile email`（模式 A） |

---

## 五、对 SSO 管理后台前端界面的建议

目前在 SSO 管理后台创建/查看 OAuth2 应用时，界面上**缺少以下关键信息的展示**，导致对接方无法直接获取配置参数，需要额外沟通确认。

**建议在"应用详情"页面增加展示以下信息**：

| 信息 | 说明 | 对接方需要复制粘贴 |
|------|------|------------------|
| **Issuer URL** | SSO 的签发者地址 | ✅ 对接方填入 `OIDC_ISSUER_URL` |
| **Discovery URL** | `{issuer}/api/v1/oauth2/.well-known/openid-configuration` | ✅ 对接方用来验证连通性 |
| **Authorization Endpoint** | 授权端点完整 URL | ✅ 对接方填入 `OIDC_AUTHORIZE_URL` |
| **Token Endpoint** | Token 端点完整 URL | ✅ 对接方填入 `OIDC_TOKEN_URL` |
| **UserInfo Endpoint** | 用户信息端点完整 URL | ✅ 对接方填入 `OIDC_USERINFO_URL` |
| **JWKS URI** | 公钥端点完整 URL | 参考（如 SSO 支持） |
| **客户端 ID** | 已有 ✅ | ✅ 对接方填入 `OIDC_CLIENT_ID` |
| **客户端密钥** | 已有 ✅（显示/隐藏切换） | ✅ 对接方填入 `OIDC_CLIENT_SECRET` |
| **支持的 Grant Types** | 如 `authorization_code`, `refresh_token` | 参考 |
| **支持的 Scopes** | 如 `openid`, `profile`, `email` | 参考 |
| **是否支持 PKCE** | 是/否 | ✅ 对接方判断是否需要传 client_secret |

理想的展示方式是在应用详情页提供一个**"第三方系统对接配置"**面板或可展开区域，把上述所有信息以**可复制**的形式列出。类似这样：

```
┌─────────────────────────────────────────────────────┐
│ 第三方系统对接配置                            [复制全部] │
│                                                     │
│ Issuer URL:         https://sso.haocai.com.cn:8080  │
│ Discovery URL:      https://sso.haocai.com.cn:8080/api/v1/oauth2/.well-known/openid-configuration │
│ Authorization:      https://sso.haocai.com.cn:8080/api/v1/oauth2/authorize │
│ Token:              https://sso.haocai.com.cn:8080/api/v1/oauth2/token │
│ UserInfo:           https://sso.haocai.com.cn:8080/api/v1/oauth2/userinfo │
│ JWKS URI:           https://sso.haocai.com.cn:8080/api/v1/oauth2/jwks │
│                                                     │
│ 客户端 ID:          nqB6VTGm...                [📋] │
│ 客户端密钥:         pQm_ZXU...       [👁 显示] [📋] │
│                                                     │
│ Grant Types:        authorization_code, refresh_token│
│ Scopes:             openid, profile, email          │
│ PKCE:               ✅ 支持 S256                     │
│ Token 签名算法:     RS256                            │
└─────────────────────────────────────────────────────┘
```

这样第三方系统对接时可以直接复制配置，无需反复沟通确认。

---

## 六、对接完成后的验证步骤

### 模式 B（当前可立即测试）

1. **确认端点可访问**：浏览器分别访问 authorize、token、userinfo 的 URL，确认不返回 404
2. **Data Formulator 侧配置**：`.env` 中设置手动端点（见第二节），重启后端
3. **观察日志**：应看到 `OIDC provider ready: ... discovery=manual, token_validation=userinfo`
4. **浏览器测试**：打开 Data Formulator → 点击 SSO Login → 跳转 SSO 登录页 → 登录 → 回调成功

### 模式 A（SSO 改进后测试）

1. **验证 Discovery**：浏览器访问 `https://sso.haocai.com.cn:8080/api/v1/oauth2/.well-known/openid-configuration`，确认返回正确 JSON
2. **验证 JWKS**：访问 discovery JSON 中 `jwks_uri` 指向的地址，确认返回包含 `keys` 数组的 JSON
3. **验证 issuer 一致**：确认 discovery JSON 中 `"issuer"` 值与实际访问地址一致
4. **Data Formulator 侧配置**：`.env` 中只需 3 个变量（`AUTH_PROVIDER`、`OIDC_ISSUER_URL`、`OIDC_CLIENT_ID`），删除手动端点配置
5. **观察日志**：应看到 `OIDC discovery succeeded` 和 `token_validation=JWKS`

---

## 七、已发现的 SSO 实现问题

### 7.1 `sub` claim 在 JWT 和 UserInfo 之间不一致（Bug）

**发现时间**：2026-04-10

**现象**：同一个用户（zhanghaibin），SSO 系统在两个地方返回了不同的 `sub` 值：

| 来源 | `sub` 值 | 实际含义 |
|------|----------|---------|
| **Access Token（JWT payload）** | `"zhanghaibin"` | 用户名 |
| **UserInfo 端点响应** | `"7"` | 数据库自增 ID |

**JWT payload 解码**（`https://sso.haocai.com.cn:8080` 签发）：

```json
{
  "sub": "zhanghaibin",
  "user_id": 7,
  "username": "zhanghaibin",
  "email": null,
  "roles": ["admin", "user"],
  "token_type": "access"
}
```

**UserInfo 端点响应**（`GET /api/v1/oauth2/userinfo`）：

```json
{
  "sub": "7",
  "preferred_username": "zhanghaibin",
  "name": "张海彬",
  "email": null,
  "roles": ["admin", "user"]
}
```

**为什么这是 Bug**：

根据 [OpenID Connect Core 1.0 §5.3](https://openid.net/specs/openid-connect-core-1_0.html#UserInfoResponse) 规范：

> The `sub` Claim in the UserInfo Response MUST be verified to exactly match the `sub` Claim in the ID Token; if they do not match, the UserInfo Response values MUST NOT be used.

`sub`（Subject Identifier）是 OIDC 中用户身份的**唯一不可变标识**，必须在所有端点中保持一致。当前 SSO 系统在 JWT 和 UserInfo 中使用了不同的值，会导致：

1. **身份识别混乱**：使用 JWKS 本地验证时用户标识为 `zhanghaibin`，使用 UserInfo 验证时标识为 `7`，同一用户在不同验证模式下被视为不同的人
2. **数据隔离错误**：Data Formulator 根据 `sub` 创建用户工作空间目录，两种模式产生不同的目录（`user_zhanghaibin` vs `user_7`），导致数据丢失
3. **违反 OIDC 规范**：任何遵循标准的 OIDC 客户端都可能出现问题

**建议修复**（SSO 侧）：

统一 `sub` 的含义。推荐方案：

| 方案 | `sub` 值 | 优缺点 |
|------|----------|--------|
| **方案 A（推荐）** | 始终使用用户名，如 `"zhanghaibin"` | 可读性好，但用户名修改后会破坏关联 |
| **方案 B** | 始终使用数据库 ID，如 `"7"` | 不可变，但可读性差 |
| **方案 C** | 使用 UUID，如 `"550e8400-..."` | 最佳实践，不可变且无信息泄漏 |

无论选哪种，**JWT 和 UserInfo 必须返回相同的值**。同时建议在 JWT 和 UserInfo 中都包含以下标准 claim：

```
sub               → 唯一标识（一致）
preferred_username → 用户登录名
name              → 显示名称
email             → 邮箱
```

### 7.2 UserInfo 响应缺少 `email` 字段

当前 UserInfo 返回 `"email": null`。虽然不影响登录，但建议 SSO 管理员确认：
- 用户是否有邮箱记录但未暴露给 OAuth2 scope
- 是否需要在 `profile` 或 `email` scope 中包含邮箱

### 7.3 Data Formulator 侧的临时解决方案

在 SSO 修复 `sub` 一致性之前，Data Formulator 提供了 `OIDC_IDENTITY_CLAIM` 配置项作为 workaround：

```bash
# .env 中添加：
OIDC_IDENTITY_CLAIM=preferred_username
```

此配置让 Data Formulator 使用 `preferred_username`（即 `"zhanghaibin"`）而非 `sub`（即 `"7"`）作为用户标识，效果：

| 配置 | UserInfo 取值 | 身份字符串 | 目录名 |
|------|-------------|-----------|--------|
| 默认（`sub`） | `"7"` | `user:7` | `user_7` |
| `preferred_username` | `"zhanghaibin"` | `user:zhanghaibin` | `user_zhanghaibin` |

> **注意**：这是临时方案。`preferred_username` 在 OIDC 规范中不保证唯一且不保证不可变。正确做法仍然是修复 SSO 侧的 `sub` 一致性。

---

## 八、Superset JWT API 权限问题排查（需 Superset 管理员协助）

> **发现时间**：2026-04-12
>
> **严重程度**：高 — 直接影响 Data Formulator 通过 API 读取 Superset 数据

### 8.1 问题现象

Data Formulator 通过 Superset REST API（JWT Bearer Token 认证）读取仪表盘和数据集时，**只能看到公共数据，无法看到需要权限的数据**。但使用同一账号通过浏览器 Web UI 登录 Superset 后，所有数据都能正常看到。

具体表现（以 admin 用户为例）：

| 指标 | 浏览器 UI 登录（正常） | JWT API 调用（异常） |
|------|---------------------|-------------------|
| 数据库 | 3 个（NC_WAREHOUSE, YaFo_B2B, YaFo_MALL） | **仅 1 个**（NC_WAREHOUSE） |
| 数据集 | 60+ 个 | **仅 3 个**（华为公共数据集） |
| 仪表盘 | 多个 | **仅 1 个** |
| `/api/v1/me/` | 正常 | **返回 401 Not authorized** |

按 ID 直接访问非公共数据集（如 `/api/v1/dataset/39`）返回 **404**（非 403），说明数据被过滤器彻底隐藏。

### 8.2 已排除的原因

以下方面均已验证正常，**不是**导致问题的原因：

| 排查项 | 结果 |
|--------|------|
| JWT token 是否有效 | ✅ 有效，`sub: "1"` 对应 admin 用户 |
| 用户是否有 Admin 角色 | ✅ admin 用户（id=1）拥有 `Admin`（id=1）和 `管理员`（id=16）两个角色 |
| 角色是否有数据权限 | ✅ 两个角色各有 312 个权限，包含 `all_datasource_access`、`all_database_access`、`all_query_access`，以及 60+ 个具体的 `datasource_access` |
| 登录 API 是否正常 | ✅ `POST /api/v1/security/login` 正常返回 token |
| token 中的用户身份 | ✅ 通过 `/api/v1/security/users/` 确认 token 对应 admin 用户 |

### 8.3 根因分析

Superset 的内置 `Admin` 角色通过**代码级别的硬编码绕过**（`is_admin()` 方法）获得全部权限，而不是通过显式的权限条目匹配。

- **浏览器 Session 认证**时：Superset 安全管理器检测到 `is_admin() == True`，直接绕过所有数据过滤器（`DatasourceFilter`、`DashboardAccessFilter`），因此能看到所有数据。
- **JWT Bearer Token 认证**时：API 的数据过滤器未正确调用 `is_admin()` 绕过逻辑，同时 JWT 认证链路中用户的安全上下文（Flask `g.user`）没有被完整加载，过滤器无法识别用户的实际权限，将其视为匿名用户，只返回公共数据。

**简言之：权限配置没问题，问题在于 Superset 处理 JWT 请求时没有正确加载用户权限。**

### 8.4 需要 Superset 管理员执行的操作

#### 操作 1：查看 Superset 版本

```bash
# 直接部署
pip show apache-superset 2>/dev/null || pip3 show apache-superset 2>/dev/null

# Docker 部署
docker exec <superset容器名> pip show apache-superset
```

请反馈版本号（如 `2.1.0`、`3.0.4`、`4.0.1` 等），不同版本的修复方式不同。

#### 操作 2：查看 `superset_config.py` 关键配置

找到 `superset_config.py` 文件：

```bash
# 常见路径
find / -name "superset_config.py" 2>/dev/null

# Docker 部署
docker exec <superset容器名> find / -name "superset_config.py" 2>/dev/null

# 常见位置：
#   /app/pythonpath/superset_config.py
#   /etc/superset/superset_config.py
#   /home/superset/superset_config.py
```

然后执行以下命令，将输出结果反馈：

```bash
grep -n -E "(AUTH_TYPE|PUBLIC_ROLE|GUEST_ROLE|FAB_API|CUSTOM_SECURITY|TALISMAN|WTF_CSRF|SESSION_COOKIE|JWT|SECRET_KEY)" superset_config.py
```

重点关注以下配置项：

| 配置项 | 期望值 | 可能导致问题的值 | 说明 |
|--------|--------|----------------|------|
| `AUTH_TYPE` | `AUTH_DB`（=1）或 `AUTH_OAUTH` | 其他值 | 决定认证方式，影响 JWT 用户加载 |
| `PUBLIC_ROLE_LIKE` | **不设置** | 如果设置了 | 可能让 JWT 用户只获得公共角色权限 |
| `GUEST_ROLE_NAME` | **不设置** | 如果设置了 | JWT 用户可能被降级为 guest |
| `TALISMAN_ENABLED` | `False` | `True` | HTTP 安全头可能干扰 JWT 传递 |
| `WTF_CSRF_ENABLED` | — | — | 通常不影响 GET 请求，但需确认 |
| `SECRET_KEY` | 已设置且稳定 | 如果频繁变更 | JWT 签名密钥，变更后旧 token 失效 |
| `FAB_ADD_SECURITY_API` | `True` | `False` | 必须为 True |
| `CUSTOM_SECURITY_MANAGER_CLASS` | — | — | 如有自定义类，需检查是否覆盖了权限加载逻辑 |

#### 操作 3：检查是否有 Data Formulator 的 SSO Bridge 配置

如果之前按照 Data Formulator 的指引在 `superset_config.py` 中添加了 `CustomSecurityManager`（包含 `df_sso_bridge` 方法），请确认该类是否正确继承了 `SupersetSecurityManager`，并检查是否有覆盖安全相关方法。

### 8.5 可能的修复方案

根据管理员反馈的配置信息，可能需要以下修复（**请勿盲目执行，需先完成操作 1-3 再确定方案**）：

#### 方案 A：确保 API 安全层正确初始化

```python
# 在 superset_config.py 中添加/确认
FAB_ADD_SECURITY_API = True

from flask_appbuilder.const import AUTH_DB
AUTH_TYPE = AUTH_DB
```

#### 方案 B：延长 JWT token 有效期（可选优化）

```python
from datetime import timedelta

# 默认 access_token 只有 15 分钟，建议延长
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
```

#### 方案 C：排除 TALISMAN 干扰

```python
# 如果 TALISMAN_ENABLED 为 True，临时禁用以排除干扰
TALISMAN_ENABLED = False
```

#### 方案 D：确保 PUBLIC_ROLE 不覆盖用户权限

```python
# 确认以下配置没有被设置为异常值
# PUBLIC_ROLE_LIKE = ""     # 不要设置
# GUEST_ROLE_NAME = ""      # 不要设置
```

> **重要**：修改 `superset_config.py` 后需要**重启 Superset 服务**才能生效。

### 8.6 修复后的验证命令

管理员修改配置并重启 Superset 后，执行以下命令验证（替换 `SUPERSET地址`、`密码`、`<TOKEN>`）：

```bash
# 步骤 1：获取 JWT token
TOKEN=$(curl -s -X POST http://SUPERSET地址:8088/api/v1/security/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"密码","provider":"db","refresh":true}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Token: ${TOKEN:0:30}..."

# 步骤 2：测试数据集列表
echo "=== Datasets ==="
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://SUPERSET地址:8088/api/v1/dataset/?q=(page:0,page_size:5)" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'count={d[\"count\"]}')"

# 步骤 3：测试仪表盘列表
echo "=== Dashboards ==="
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://SUPERSET地址:8088/api/v1/dashboard/?q=(page:0,page_size:5)" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'count={d[\"count\"]}')"

# 步骤 4：测试 /api/v1/me/
echo "=== Me ==="
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://SUPERSET地址:8088/api/v1/me/" \
  | python3 -m json.tool
```

**验证通过的标志**：

| 检查项 | 修复前 | 修复后应为 |
|--------|--------|----------|
| 数据集 count | 3 | **60+** |
| 仪表盘 count | 1 | **多个** |
| `/api/v1/me/` | 401 | **返回用户信息 JSON** |

---

## 九、总结

| SSO 侧需要做的 | 复杂度 | 优先级 | 是否必须 |
|----------------|--------|--------|---------|
| **当前什么都不改** — 使用模式 B 手动端点对接 | 无 | — | ✅ 立即可用 |
| **修复 `sub` claim 一致性**（JWT 与 UserInfo 返回相同值） | 低（改代码逻辑） | **高** | ⚠️ 强烈建议（当前有 Bug） |
| 加 `/api/v1/oauth2/.well-known/openid-configuration` 端点 | 低（静态 JSON） | 推荐 | 可选（简化配置） |
| 加 JWKS 公钥端点 | 低（框架通常内置） | 推荐 | 可选（提升性能） |
| issuer 改为外部地址 | 低（改配置） | 推荐 | 仅 JWKS 模式需要 |
| 支持 PKCE | 中 | 推荐 | 可选（提升安全性） |
| 管理后台展示对接配置信息 | 中 | 推荐 | 可选（提升对接效率） |

| Superset 侧需要做的 | 复杂度 | 优先级 | 是否必须 |
|--------------------|--------|--------|---------|
| **反馈 Superset 版本号**（见 8.4 操作 1） | 无 | **最高** | ✅ 必须 |
| **反馈 `superset_config.py` 关键配置项**（见 8.4 操作 2） | 低（执行 grep） | **最高** | ✅ 必须 |
| **检查 CustomSecurityManager**（见 8.4 操作 3） | 低（查看代码） | **高** | ✅ 如有自定义类 |
| 按修复方案调整 `superset_config.py` 并重启 | 低（改配置+重启） | **高** | ✅ 待确认方案后执行 |
| 执行验证命令确认修复（见 8.6） | 低（执行命令） | **高** | ✅ 修复后执行 |
