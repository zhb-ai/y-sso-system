# 版本升级与对接说明

> 适用范围：本次引入 `public/confidential` 客户端类型、`PKCE`、`OIDC id_token/nonce`、`RS256 + JWKS`、应用对接信息面板的升级版本。

> 注意：本文档面向**已有部署的升级场景**。如果是全新安装，请以 `README.md` 中的首次安装流程为准，执行 `alembic upgrade head` 后再运行 `python init_db.py`。

## 一、本次升级包含的关键变更

本次版本不是单纯的界面调整，而是一次 OAuth2 / OIDC 能力升级，重点包括：

- 应用新增客户端类型：`confidential` / `public`
- `public` 客户端支持并强制要求 `PKCE(S256)`
- OIDC 授权流程支持 `nonce`
- 当 `scope` 包含 `openid` 时，`token` / `refresh_token` 流程会返回 `id_token`
- 默认签名配置调整为 `RS256`，并新增 `JWKS` 公钥端点
- 新增 Discovery 端点 `/api/v1/oauth2/.well-known/openid-configuration`
- 管理后台应用页可直接查看主要对接信息

同时，本次版本对下游系统有两个需要特别关注的兼容性点：

- `sub` 已统一为用户 ID 字符串，请不要再把旧版本中的用户名形式 `sub` 当作长期主键
- 浏览器 SPA / 原生客户端不应再把 `client_secret` 放在前端，应改为 `public + PKCE`

## 二、升级前检查

升级前请先完成以下检查：

1. 备份当前数据库，尤其是生产环境。
2. 确认所有下游系统当前使用哪种客户端形态：
   - 服务端 Web 应用：通常使用 `confidential`
   - 浏览器 SPA / 原生客户端：建议改为 `public`
3. 确认下游系统是否把 `sub` 持久化为业务主键、目录名、缓存键或工作空间标识。
4. 确认部署环境中 `base_url` 为真实外部访问地址，而不是 `localhost`。
5. 确认生产环境已准备自己的 RSA 密钥对，不要继续使用仓库中的开发密钥。

## 三、必须执行的升级步骤

### 1. 更新代码并安装依赖

```bash
pip install -r requirements.txt
```

本次依赖中新增/明确使用了以下能力：

- `python-jose[cryptography]`
- `cryptography`

### 2. 更新配置文件

请对照 `config/settings.yaml_demo` 检查你的 `config/settings.yaml`，至少确认以下配置：

```yaml
jwt:
  secret_key: "dev-rs256-key-placeholder"
  algorithm: RS256
  access_token_expire_minutes: 30
  refresh_token_expire_days: 7
  refresh_token_sliding_days: 2

jwt_private_key_path: "config/dev-keys/jwt_private.pem"
jwt_public_key_path: "config/dev-keys/jwt_public.pem"
jwt_key_id: "sso-dev-rs256-key-1"

base_url: "https://your-sso.example.com"
oidc_issuer: "https://your-sso.example.com/api/v1/oauth2"
```

需要重点关注的配置项：

- `jwt.algorithm`
  - 本次推荐并默认使用 `RS256`
- `jwt_private_key_path`
  - JWT 签名私钥路径
- `jwt_public_key_path`
  - JWKS 暴露给下游的公钥路径
- `jwt_key_id`
  - JWKS 中的 `kid`
- `base_url`
  - 系统对外根地址
- `oidc_issuer`
  - OIDC issuer 标识
  - 默认建议配置为 `${base_url}/api/v1/oauth2`
  - 下游如果按 issuer 自动发现，应该使用这个值而不是根地址

> 生产环境必须替换为自己的 RSA 密钥，不可使用仓库中的开发密钥文件。

### 3. 执行数据库迁移

```bash
alembic upgrade head
```

本次数据库升级涉及以下迁移：

- `efc5e98f7dfa`
  - `application.client_type`
  - `authorization_code.code_challenge`
  - `authorization_code.code_challenge_method`
- `6c1d8e4a7b21`
  - `authorization_code.nonce`

如果跳过迁移，会直接影响以下能力：

- 无法保存应用客户端类型
- `public` 客户端无法完成 PKCE 流程
- OIDC `nonce` 无法持久化，`id_token` 流程不完整

### 4. 重启服务

修改配置或密钥后，必须重启后端服务。若前端已部署，也建议同步更新前端静态资源。

开发环境默认后端端口统一为 `8000`。如果你还有旧脚本、反向代理或联调配置写的是 `8001`，请一并检查。

## 四、数据库字段变化说明

### `application` 表

新增字段：

- `client_type`
  - 取值：`confidential` / `public`
  - 默认值：`confidential`

含义：

- `confidential`
  - 适用于服务端应用
  - 使用 `client_secret`
- `public`
  - 适用于浏览器 SPA、移动端、桌面端等不适合保存密钥的客户端
  - 不使用 `client_secret`
  - 授权码换 token 时必须使用 `PKCE(S256)`

### `authorization_code` 表

新增字段：

- `nonce`
- `code_challenge`
- `code_challenge_method`

这些字段分别用于：

- `nonce`
  - 支持 OIDC 授权请求与 `id_token` 返回
- `code_challenge` / `code_challenge_method`
  - 支持 PKCE 授权码交换

## 五、下游系统如何选择客户端类型

### 选择 `confidential`

适用场景：

- 传统服务端 Web 应用
- 后端可安全保存 `client_secret`
- 由服务端发起授权码换 token

对接要求：

- 必须保存并传递 `client_secret`
- 可以继续使用传统授权码流程
- 如有需要，也可以额外启用 PKCE

### 选择 `public`

适用场景：

- 浏览器 SPA
- 移动端 App
- 桌面客户端
- 任何无法安全保存 `client_secret` 的前端场景

对接要求：

- 不使用 `client_secret`
- 授权请求必须携带：
  - `code_challenge`
  - `code_challenge_method=S256`
- `token` 交换时必须携带：
  - `code_verifier`

> 如果当前某个浏览器项目把 `client_secret` 放在前端代码、环境变量或浏览器请求中，本次升级后建议尽快切换到 `public + PKCE`。

## 六、OIDC / PKCE / JWKS 对接方式

### 1. 推荐优先使用 Discovery

本次版本提供标准 Discovery 端点：

- `/api/v1/oauth2/.well-known/openid-configuration`

返回内容中会包含：

- `issuer`
- `authorization_endpoint`
- `token_endpoint`
- `userinfo_endpoint`
- `jwks_uri`
- `code_challenge_methods_supported`

如果下游系统支持 OIDC 自动发现，优先只配置 `issuer` 或 `discovery URL`。

### 2. 手动对接时使用的端点

如果下游系统不支持自动发现，可手动配置以下端点：

- `issuer`: `${oidc_issuer}`
- `discovery_url`: `${oidc_issuer}/.well-known/openid-configuration`
- `authorization_endpoint`: `${oidc_issuer}/authorize`
- `token_endpoint`: `${oidc_issuer}/token`
- `userinfo_endpoint`: `${oidc_issuer}/userinfo`
- `jwks_uri`: `${oidc_issuer}/jwks`

管理后台也提供：

- `GET /api/v1/settings/oauth2-endpoints`

可用于实施同学快速复制当前系统支持能力和对接地址。

### 3. OIDC 行为说明

当授权请求的 `scope` 包含 `openid` 时：

- `token` 接口会返回 `id_token`
- `id_token` 中会包含：
  - `iss`
  - `aud`
  - `sub`
  - `preferred_username`
  - `email`
  - `nonce`（如果授权请求中传入）

请注意：

- `sub` 现在统一为用户 ID 字符串
- `iss` 现在使用 `oidc_issuer`（默认是 `${base_url}/api/v1/oauth2`）
- 下游系统如果之前拿用户名当 `sub`，本次升级后应改为使用标准 `sub`
- 需要展示用户名时，请读取 `preferred_username`

### 4. JWKS 使用说明

当系统启用 `RS256` 且配置了有效公钥后，会暴露：

- `/api/v1/oauth2/jwks`

适用场景：

- 下游需要本地验签 `id_token` / `access_token`
- 希望减少频繁调用 `userinfo` 带来的回源依赖

注意事项：

- 下游验签时，应同时校验 `iss`、`aud`、签名算法、过期时间
- `aud` 取值为当前客户端的 `client_id`
- `kid` 来自 `jwt_key_id`

### 5. PKCE 参数要求

本次仅支持：

- `code_challenge_method=S256`

不支持：

- `plain`

也就是说：

- `public` 客户端必须启用 `PKCE(S256)`
- `confidential` 客户端如果传了 `code_challenge`，也必须是 `S256`

## 七、独立开发者对接文档

面向 `Data Formulator` 与 `Superset` 程序员的项目内配置说明，已单独整理到：

- [`docs/df-superset-developer-integration-guide.md`](docs/df-superset-developer-integration-guide.md)

该文档专门说明：

- `DF` 需要在自己的项目里改哪些文件、设置哪些变量
- `Superset` 需要在自己的项目里改哪些文件、设置哪些变量
- `SSO` 后台分别要给 `DF` 和 `Superset` 创建什么客户端
- 两边各自该登记什么回调地址

## 八、升级后建议执行的验证

### 1. 验证迁移已生效

```bash
alembic current
```

预期结果：当前 revision 为最新 `head`。

### 2. 验证 Discovery / JWKS

```bash
curl http://localhost:8000/api/v1/oauth2/.well-known/openid-configuration
curl http://localhost:8000/api/v1/oauth2/jwks
curl http://localhost:8000/api/v1/settings/oauth2-endpoints
```

至少应确认：

- Discovery 返回 `issuer`
- Discovery 返回 `code_challenge_methods_supported: ["S256"]`
- Discovery 返回非空 `jwks_uri`
- JWKS 返回非空 `keys`
- `oauth2-endpoints` 返回 `pkce_supported=true`

### 3. 验证应用管理后台

在应用管理页确认以下信息展示正常：

- 客户端类型
- 客户端 ID
- Discovery URL
- Authorization / Token / UserInfo / JWKS 地址
- PKCE 支持状态
- Token 签名算法

### 4. 验证下游真实登录流程

建议至少覆盖两类场景：

1. `confidential` 客户端：
   - 授权码换 token 成功
   - 携带 `client_secret`
2. `public` 客户端：
   - 授权码换 token 成功
   - 不携带 `client_secret`
   - 携带正确的 `code_verifier`

## 九、升级时最容易遗漏的事项

- 只更新代码，没有执行 `alembic upgrade head`
- 只改了 `jwt.algorithm=RS256`，但没有配置私钥/公钥路径
- `base_url` 仍然是 `localhost`，导致下游校验 `issuer` 失败
- 浏览器客户端仍在使用 `client_secret`
- 下游系统继续把旧版本中的用户名形式 `sub` 当主键
- 生产环境误用了仓库中的开发 RSA 密钥

## 十、建议的发布通知重点

如果你要把这次升级同步给实施或下游开发，建议至少明确以下内容：

1. 本次升级需要执行数据库迁移。
2. 本次升级默认采用 `RS256 + JWKS`。
3. 本次升级新增 `public/confidential` 客户端类型。
4. 浏览器客户端建议改为 `public + PKCE(S256)`。
5. `sub` 已统一为用户 ID 字符串，请检查下游映射逻辑。
