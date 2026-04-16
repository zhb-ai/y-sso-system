# OIDC RS256 JWKS Design

**目标：** 让 `y-sso-system` 在默认开发环境下直接具备完整的 `Discovery + JWKS + JWKS 验签` 能力，使 `GET /api/v1/settings/oauth2-endpoints` 中的 `JWKS URI` 不再显示“当前未启用”，并为用户提供明确的密钥生成与配置文档。

## 背景

当前 `y-sso-system` 已经具备以下基础能力：

- 已实现 `/.well-known/openid-configuration`
- 已实现 `GET /api/v1/oauth2/jwks`
- 已在 OAuth2 token 生成逻辑中写入 `iss` 和 `aud`
- 已支持 PKCE

但默认运行配置仍是 `HS256`，且没有配置 RSA 公私钥路径，因此：

- `Discovery` 默认不会声明 `jwks_uri`
- `oauth2-endpoints` 页面中的 `JWKS URI` 显示为未启用
- 下游系统无法通过 `JWKS` 在本地完成 JWT 签名验证

目标不是新增全新的 OIDC 能力，而是把现有代码中的能力默认启用，并补齐开发联调与用户文档。

## 设计决策

### 配置策略

- 采用方案 1：在仓库中提供一套**仅用于开发环境**的 RSA 密钥文件
- 默认开发配置切换到 `RS256`
- `config/settings.yaml` 中显式配置：
  - `jwt.algorithm=RS256`
  - `jwt_private_key_path`
  - `jwt_public_key_path`
  - 可选保留 `jwt_key_id`
- `base_url` 继续作为 OIDC `issuer` 与 JWT `iss` 的来源

这样做的原因：

- 本地开发与联调时，`JWKS` 内容稳定，不会因为服务重启而变化
- `kid` 稳定，便于下游缓存和排查问题
- `oauth2-endpoints` 页面、Discovery 文档和实际令牌签名能力保持一致

### 密钥文件策略

- 在项目内新增开发专用 RSA 密钥文件，例如放在 `config/dev-keys/`
- 文件仅服务于本地开发、联调、自动化测试示例，不可作为生产密钥使用
- README 与配置文档中明确说明：
  - 生产环境必须替换为自有密钥
  - 不得在生产继续使用仓库内开发密钥

### 运行时行为

- `build_runtime_jwt_settings()` 继续从 `settings` 读取运行时算法和密钥
- 当 `algorithm=RS256` 且配置了有效公钥时：
  - `/.well-known/openid-configuration` 返回 `jwks_uri`
  - `/.well-known/openid-configuration` 返回 `id_token_signing_alg_values_supported=["RS256"]`
  - `GET /api/v1/oauth2/jwks` 返回真实 RSA 公钥 JWK
  - `GET /api/v1/settings/oauth2-endpoints` 返回非空 `jwks_uri`
- `OAuth2ProviderService.exchange_code_for_token()` 继续在 access token 中写入：
  - `iss=settings.base_url.rstrip("/")`
  - `aud=client_id`

### 文档策略

- 更新 `README.md`
- 如项目已有配置文档入口，也同步补充 `RS256/JWKS` 配置说明
- 文档必须覆盖以下内容：
  - 当前默认开发环境已启用 `RS256 + JWKS`
  - 如何使用 `openssl` 生成 RSA 私钥、公钥
  - 生成后的文件应放在哪个目录
  - `settings.yaml` 中应如何配置
  - 修改配置后需要重启服务
  - 生产环境如何替换为正式密钥
  - 如何验证 `Discovery` 和 `JWKS` 是否生效

## 实现范围

### 后端配置与资源

- 更新 `config/settings.yaml`
- 如有必要，同步更新 `config/settings.yaml_demo`
- 新增开发专用 RSA 密钥文件
- 如 README 中有默认算法示例，同步从 `HS256` 调整为开发环境默认 `RS256`

### 后端代码

预期代码改动应尽量小，优先复用现有能力：

- `app/services/oauth2_security.py`
  - 仅在必要时补强密钥读取、错误提示或兼容行为
- `app/api/v1/config.py`
  - 保持现有 `jwks_uri` 判定逻辑，但在默认配置下应自然返回已启用状态
- `app/main.py`
  - 保持现有 Discovery 输出逻辑，但在默认配置下应自然声明 `jwks_uri`

如果现有代码已经满足行为要求，则不做无关重构。

### 文档

- `README.md` 增加一个明确章节，建议名称类似：
  - `OIDC Discovery + JWKS 配置`
  - 或 `开发环境 RS256/JWKS 说明`
- 文档中给出可直接执行的命令示例，例如：
  - 生成私钥
  - 从私钥导出公钥
  - 配置路径
  - 验证接口

## 错误处理与约束

- 若配置为 `RS256` 但密钥路径不存在，应保证接口行为可诊断：
  - `JWKS URI` 不应谎报可用
  - 文档需提示用户检查密钥路径和文件内容
- 不引入自动生成临时密钥的隐式行为，避免：
  - 重启后 key 变化
  - `kid` 不稳定
  - 已签发 token 突然失效
- 不修改现有 OAuth2/PKCE 主流程语义
- 不引入生产环境专有逻辑，本次只解决默认开发联调配置与文档问题

## 测试策略

遵循 TDD，先写失败测试，再补实现与配置。

### 需要覆盖的测试

- API 测试：
  - 默认配置下 `GET /api/v1/settings/oauth2-endpoints` 返回非空 `jwks_uri`
  - 默认配置下 `token_signing_algorithm` 为 `RS256`
- Discovery 测试：
  - 默认配置下 `/.well-known/openid-configuration` 包含 `jwks_uri`
  - 默认配置下 `id_token_signing_alg_values_supported=["RS256"]`
- JWKS 测试：
  - 默认配置下 `GET /api/v1/oauth2/jwks` 返回至少一个 `RSA` key
  - `kid`、`alg`、`n`、`e` 字段存在且格式正确

### 回归关注

- 现有基于 monkeypatch 的 `RS256` 测试继续通过
- 现有 `HS256` 兼容逻辑不被破坏
- token 生成时的 `iss`、`aud` 行为保持不变

## 验收标准

完成后应满足：

1. 本地使用默认 `settings.yaml` 启动服务后，`GET /api/v1/settings/oauth2-endpoints` 中 `jwks_uri` 非空
2. `GET /.well-known/openid-configuration` 返回 `jwks_uri`
3. `GET /api/v1/oauth2/jwks` 返回非空 `keys`
4. `token_signing_algorithm` 显示为 `RS256`
5. README 中包含完整的密钥生成、替换和配置步骤
6. 相关 pytest 测试通过

## 影响范围

- 配置：`config/settings.yaml`，可能包括 `config/settings.yaml_demo`
- 安全辅助：`app/services/oauth2_security.py`
- 设置接口：`app/api/v1/config.py`
- Discovery 端点：`app/main.py`
- 文档：`README.md`
- 测试：`tests/test_api/test_oidc_discovery.py`、`tests/test_api/test_settings_oauth2_endpoints.py`

## 非目标

- 不在本次中改造生产部署流程
- 不在本次中实现自动轮换密钥
- 不在本次中为多个 `kid` 提供历史公钥集合
- 不在本次中修改 `data-formulator-dev`
