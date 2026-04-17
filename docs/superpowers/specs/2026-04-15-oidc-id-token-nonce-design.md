# OIDC ID Token Nonce Design

**目标：** 将 `y-sso-system` 当前的 OAuth2 Authorization Code + PKCE 实现补齐为可被标准前端 OIDC SDK 正常消费的 OpenID Connect Authorization Code Flow：支持 `nonce` 透传与保存，在 `authorization_code` 和 `refresh_token` 换发令牌时返回标准 `id_token`。

## 背景

当前 `y-sso-system` 已经具备：

- `/.well-known/openid-configuration`
- `JWKS` 公钥端点
- `RS256` 签名
- `Authorization Code + PKCE`
- `userinfo` 端点

但目前仍存在一个关键协议缺口：

- `scope` 包含 `openid` 时，`/api/v1/oauth2/token` 只返回 `access_token` / `refresh_token`
- 未返回 `id_token`
- 授权码实体未保存 `nonce`

这使得像 `Data Formulator` 这类使用 `oidc-client-ts` 的前端 OIDC 客户端无法完成标准回调处理，表现为：

- `No matching state found in storage`
- `Invalid token specified: missing part #2`

根因不是 Discovery/JWKS 本身，而是 `Token Response` 还不满足 OIDC 对 `openid` 请求的预期。

## 标准结论

本次实现遵循的关键协议结论：

- 当认证请求包含 `scope=openid` 且走 `Authorization Code Flow` 时，客户端会在 `Token Endpoint` 获取 `Access Token` 与 `ID Token`
- `nonce` 在纯 `response_type=code` 流中不是绝对必填
- 但如果客户端传入了 `nonce`，则返回的 `id_token` 中应原样带回 `nonce`
- `id_token` 必须是 JWT，并应由当前 Discovery/JWKS 所声明的算法签名

## 设计决策

### 1. 协议范围

本次补齐范围限定为：

- `GET /api/v1/oauth2/authorize` 接收 `nonce`
- `POST /api/v1/oauth2/authorize` 接收 `nonce`
- `AuthorizationCode` 持久化 `nonce`
- `POST /api/v1/oauth2/token` 在以下场景返回 `id_token`：
  - `grant_type=authorization_code`
  - `grant_type=refresh_token`

不做的内容：

- 不新增 Hybrid Flow（如 `response_type=code id_token`）
- 不新增 `end_session_endpoint`
- 不在本次中实现多历史 `kid` 或密钥轮换

### 2. `nonce` 处理

- 在授权入口透传 `nonce`
- 如果请求方传入 `nonce`，则保存到 `AuthorizationCode`
- 生成 `id_token` 时：
  - `authorization_code` 场景：若授权码上存在 `nonce`，则写入 `id_token.nonce`
  - `refresh_token` 场景：不复用旧 `nonce`，新的 `id_token` 不带 `nonce`

这样做的原因：

- 符合前端 OIDC SDK 对首次认证回调的预期
- 避免在 refresh 场景中延续一次性认证上下文
- 兼容现有授权码生命周期模型

### 3. `id_token` 内容

`id_token` 使用当前 `JWTManager` 与现有 `RS256` 配置签名，至少包含：

- `sub`
- `iss`
- `aud`
- `exp`
- `iat`
- `nonce`（若授权请求中存在）
- `name`
- `email`
- `preferred_username`

其中约束如下：

- `sub` 必须与 `userinfo.sub` 一致
- `iss` 使用 `settings.base_url.rstrip("/")`
- `aud` 使用当前 `client_id`
- `name` / `email` / `preferred_username` 直接来自当前已解析出的用户实体

### 4. Token Response 结构

#### `authorization_code`

当前返回：

- `access_token`
- `token_type`
- `expires_in`
- `refresh_token`
- `scope`

当授权请求语义属于 OIDC（即客户端走 `scope=openid` 链路）时，本次补齐后新增：

- `id_token`

#### `refresh_token`

当前返回：

- `access_token`
- `token_type`
- `expires_in`
- 条件性 `refresh_token`

为满足当前 OIDC 客户端续签兼容性，本次补齐后新增：

- `id_token`

### 5. 代码结构

预期以最小改动复用现有服务层：

- `app/domain/application/entities.py`
  - 为 `AuthorizationCode` 新增 `nonce` 字段
  - `create_code()` 接受并保存 `nonce`
- 数据库迁移
  - 需要新增 Alembic 迁移，为 `authorization_code` 表添加可空 `nonce` 列
  - 该列应保持可空，确保历史授权码数据不需要回填
- `app/api/v1/oauth2.py`
  - `AuthorizeConfirmRequest` 新增 `nonce`
  - 在 `GET /authorize` 接受 `nonce`
  - 在 `POST /authorize` 请求体接受 `nonce`
  - 将 `nonce` 传给服务层
- `app/domain/application/services.py`
  - `validate_authorize_request()` 接受 `nonce` 但不强制校验
  - `create_authorization_code()` 接受 `nonce`
  - `exchange_code_for_token()` 返回 `id_token`
  - `refresh_access_token()` 返回新的 `id_token`
  - 新增一个内部辅助函数，统一构造 `id_token` payload

如果现有 `JWTManager` 已可直接创建 Access/Refresh Token，则 `id_token` 应尽量沿用同一签名设施，不另起一套签名实现。

## 错误处理与兼容性

- 未传 `nonce` 时：
  - 授权流程仍可继续
  - 返回的 `id_token` 不带 `nonce`
- 客户端未请求 `openid` 时：
  - 本次实现目标不是扩展纯 OAuth2 客户端语义
  - `authorization_code` 场景至少要保证 `scope` 含 `openid` 时返回 `id_token`
  - 若现有实现为了兼容 refresh 简化而在部分非 `openid` 场景也返回 `id_token`，不作为本次阻塞项，但不应破坏 OIDC 主链路
- `refresh_token` 无效时：
  - 维持当前错误行为，不新增特殊分支

兼容性目标：

- 不破坏当前 `PKCE` 逻辑
- 不破坏现有 `access_token` / `userinfo` / `JWKS` 行为
- 不改变已存在的 `iss` / `aud` 注入逻辑

## 测试策略

遵循 TDD。

### Service 测试

至少覆盖：

- `authorization_code` 换 token 时返回 `id_token`
- 当授权码保存了 `nonce` 时，`id_token` payload 含相同 `nonce`
- `id_token.sub` 与现有 `userinfo.sub` 语义一致
- `refresh_token` 刷新时返回新的 `id_token`
- refresh 返回的 `id_token` 不带旧 `nonce`
- Alembic 迁移可执行，且历史数据不因新增可空列受影响

### API / 路由测试

至少覆盖：

- `GET /authorize` 能接收 `nonce` 并透传到登录页
- `POST /authorize` 能接收 `nonce` 并透传到授权码创建逻辑
- `/token` 响应包含 `id_token`

### 回归关注

- 现有 public client + PKCE 测试继续通过
- 现有 `sub` 一致性测试不回退
- 现有 `Discovery/JWKS` 测试继续通过

## 验收标准

完成后应满足：

1. `authorization_code` 换 token 时，响应中包含 `id_token`
2. `refresh_token` 刷新时，响应中包含新的 `id_token`
3. 首次认证请求若带 `nonce`，则 `id_token` 中包含同值 `nonce`
4. `id_token` 可被当前 `JWKS` 正常验签
5. `id_token.sub` 与 `userinfo.sub` 一致
6. `Data Formulator` 的 OIDC 登录回调可继续向前推进，不再因缺失 `id_token` 直接失败
7. 新增与修改的 pytest 用例通过

## 影响范围

- 领域实体：`app/domain/application/entities.py`
- 服务层：`app/domain/application/services.py`
- API 层：`app/api/v1/oauth2.py`
- 数据库迁移：`alembic/versions/*`
- 测试：`tests/test_services/test_oauth2_provider_service.py`
- 可能新增：`tests/test_api/test_oauth2_provider_api.py`

## 非目标

- 不改造 `Data Formulator`
- 不新增后端 session 模式
- 不实现 Hybrid / Implicit Flow
- 不处理生产多租户客户端建模
