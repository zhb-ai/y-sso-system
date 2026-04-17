# 单点登录系统

基于 `FastAPI + Vue 3` 的企业级单点登录平台，提供统一认证、应用接入管理、基础 OAuth2/OIDC Provider 能力、企业微信登录与组织同步能力。

当前仓库更适合作为：

- 企业内网 SSO 基座
- 私有部署身份认证中心
- 二次开发的 OAuth2/OIDC 起点

如果你的目标是“开箱即用的完整生产级 IdP”，请先阅读本文的“已知限制”和“安全建议”。

## 功能概览

- 统一认证
  - 用户名/密码登录
  - Access Token / Refresh Token
  - 首次登录强制改密
  - 登录记录与踢人下线
- OAuth2 / OIDC
  - Authorization Code Flow
  - `public` / `confidential` 客户端
  - `public` 客户端强制 `PKCE(S256)`
  - `openid` 场景返回 `id_token`
  - `nonce`
  - Discovery
  - JWKS
  - UserInfo
- 应用接入管理
  - 应用注册、启停、软删除
  - `client_secret` 查看与重置
  - `redirect_uri` 管理
  - 应用级 IP 白名单
  - 管理台对接信息面板
- 组织与权限
  - RBAC
  - SSO 角色
  - 组织架构与员工账号
- 企业微信集成
  - 企微扫码登录
  - 企微内部静默授权 URL
  - 通讯录同步与 webhook

## 当前实现定位

当前实现已经具备一条完整的基础 OIDC 主链路，但仍属于“基础可用版”而非“完整生产级标准 IdP”。

已实现的关键能力：

- `/api/v1/oauth2/authorize`
- `/api/v1/oauth2/token`
- `/api/v1/oauth2/userinfo`
- `/api/v1/oauth2/.well-known/openid-configuration`
- `/api/v1/oauth2/jwks`
- `/api/v1/settings/oauth2-endpoints`

仍建议在正式对外发布前重点补齐：

- 标准 `LICENSE` 文件
- 依赖来源说明，尤其是 `yweb`
- Docker / CI
- 更完整的 OIDC 外围能力，例如标准 revocation / introspection / logout

## 技术栈

### 后端

- `FastAPI`
- `SQLAlchemy`
- `Alembic`
- `python-jose`
- `cryptography`
- `Redis`（可选）
- `yweb`

### 前端

- `Vue 3`
- `Vite`
- `Pinia`
- `Axios`
- `Element Plus`

## 架构概览

项目采用 `API -> Service -> Domain` 的分层结构：

- `app/api`
  - 提供 REST API、OAuth2/OIDC 端点、中间件、路由注册
- `app/domain`
  - 承载应用管理、认证、权限、组织架构、企业微信等领域逻辑
- `app/services`
  - 提供协议安全辅助与跨模块应用服务
- `frontend`
  - 管理后台、登录页、SSO 授权页、应用接入配置页

默认后端通过 `FastAPI` 提供 API 与静态资源，前端开发态通过 `Vite` 单独启动。

## 快速开始

### 环境要求

- Python `3.11+`
- Node.js `16+`
- Redis `6+`（可选）
- OpenSSL（推荐，用于生成 RSA 密钥）

### 1. 获取代码

```bash
git clone https://github.com/zhb-ai/y-sso-system.git
cd y-sso-system
```

### 2. 创建虚拟环境并安装依赖

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
pip install -r requirements.txt
```

Linux / macOS:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

注意：

- 本项目通过 `requirements.txt` 直接从公开仓库安装并固定 `yweb 0.1.3`
- 对应仓库为 `https://github.com/yafo-ai/yweb-core`
- 如需单独安装，也可以执行 `pip install "yweb @ git+https://github.com/yafo-ai/yweb-core.git@0.1.3"`

### 3. 复制配置文件

仓库默认只有示例配置，请先复制：

```bash
copy config\settings.yaml_demo config\settings.yaml
```

Linux / macOS:

```bash
cp config/settings.yaml_demo config/settings.yaml
```

至少需要检查这些配置项：

```yaml
base_url: "http://localhost:8000"
oidc_issuer: "http://localhost:8000/api/v1/oauth2"

jwt:
  algorithm: RS256

jwt_private_key_path: "config/dev-keys/jwt_private.pem"
jwt_public_key_path: "config/dev-keys/jwt_public.pem"
jwt_key_id: "sso-dev-rs256-key-1"

database:
  url: sqlite:///./app/db/y_sso.db
```

### 4. 准备 RSA 密钥

仓库当前不包含默认开发密钥文件，需要自行生成。

Windows / Linux / macOS 均可使用：

```bash
mkdir config/dev-keys
openssl genrsa -out config/dev-keys/jwt_private.pem 2048
openssl rsa -in config/dev-keys/jwt_private.pem -pubout -out config/dev-keys/jwt_public.pem
```

如果你修改了路径，请同步更新 `config/settings.yaml` 中的：

- `jwt_private_key_path`
- `jwt_public_key_path`
- `jwt_key_id`

说明：

- `jwt_key_id` 主要用于 `JWKS` / `id_token` 头部中的 `kid`
- 如果运行环境中的 `yweb` 版本较旧、不支持在 `JWTManager` 中注入 `key_id`，系统会自动忽略该参数，不影响启动

### 5. 初始化数据库

首次安装建议先执行迁移，再初始化基础数据：

```bash
alembic upgrade head
python init_db.py
```

### 6. 启动后端

推荐使用开发启动脚本：

```bash
python dev_server.py --port 8000
```

或直接使用 `uvicorn`：

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 7. 启动前端

首次运行：

```bash
cd frontend
npm install
```

启动开发服务器：

```bash
npm run dev
```

### 8. 前后端开发端口

当前默认开发口径统一为：

- 后端：`8000`
- 前端：`5200`
- `frontend/vite.config.js` 的 `/api` 代理默认指向 `http://localhost:8000`

如果你自行修改后端端口，请同步更新：

- `config/settings.yaml`
- `frontend/vite.config.js`
- 所有需要手工配置 issuer 的下游系统

### 9. 访问入口

- 管理后台：`http://localhost:5200`
- 登录页：`http://localhost:5200/login`
- SSO 门户：`http://localhost:5200/sso/login`
- Swagger：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`

## OAuth2 / OIDC 对接

### 已支持能力

- Authorization Code Flow
- `public` / `confidential` 客户端
- `public + PKCE(S256)`
- `openid` + `id_token`
- `nonce`
- Discovery
- JWKS
- UserInfo

### 推荐接入方式

优先使用 Discovery：

- `/api/v1/oauth2/.well-known/openid-configuration`

也可以通过管理端接口获取对接信息：

- `GET /api/v1/settings/oauth2-endpoints`

### 关键端点

- `GET /api/v1/oauth2/authorize`
- `POST /api/v1/oauth2/authorize`
- `POST /api/v1/oauth2/token`
- `GET /api/v1/oauth2/userinfo`
- `GET /api/v1/oauth2/.well-known/oauth-authorization-server`
- `GET /api/v1/oauth2/jwks`

### 客户端类型说明

- `confidential`
  - 适合服务端 Web 应用
  - 通过 `client_secret` 参与 token 交换
- `public`
  - 适合浏览器 SPA、移动端、桌面端
  - 不使用 `client_secret`
  - 必须使用 `PKCE(S256)`

### OIDC 行为说明

- `issuer` 默认是 `oidc_issuer`
- 如果未单独配置 `oidc_issuer`，系统会默认使用 `${base_url}/api/v1/oauth2`

当授权请求中的 `scope` 包含 `openid` 时：

- `token` 响应会返回 `id_token`
- `id_token` 包含 `iss`、`aud`、`sub`、`preferred_username`、`email`
- 如果授权请求携带了 `nonce`，会回传到 `id_token`

更详细的升级与接入说明请见：

- [`docs/version-upgrade-and-integration-guide.md`](docs/version-upgrade-and-integration-guide.md)

## 主要 API

完整接口请以 Swagger `/docs` 为准。下面只列出最常用的真实路径。

### 认证

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/change-password`
- `GET /api/v1/auth/wechat-work/login-config`
- `POST /api/v1/auth/wechat-work/login`
- `GET /api/v1/auth/wechat-work/oauth-url`

### 应用管理

- `GET /api/v1/applications/list`
- `GET /api/v1/applications/get`
- `GET /api/v1/applications/secret`
- `POST /api/v1/applications/create`
- `POST /api/v1/applications/update`
- `POST /api/v1/applications/delete`
- `POST /api/v1/applications/enable`
- `POST /api/v1/applications/disable`
- `POST /api/v1/applications/reset-secret`

### 企业微信同步

- `POST /api/v1/wechat-work/config/bind`
- `POST /api/v1/wechat-work/config/unbind`
- `GET /api/v1/wechat-work/config/get`
- `POST /api/v1/wechat-work/sync/init`
- `POST /api/v1/wechat-work/sync/manual`
- `GET /api/v1/wechat-work/sync/status`
- `GET /api/v1/wechat-work/webhook/{org_id}`
- `POST /api/v1/wechat-work/webhook/{org_id}`

## 项目结构

```text
y-sso-system/
├── app/
│   ├── api/
│   ├── domain/
│   ├── services/
│   ├── config.py
│   └── main.py
├── config/
│   └── settings.yaml_demo
├── frontend/
├── alembic/
├── tests/
├── docs/
├── init_db.py
├── dev_server.py
└── requirements.txt
```

## 测试

运行全部测试：

```bash
pytest
```

运行 OAuth2 / OIDC 相关测试：

```bash
pytest tests/test_api/test_oidc_discovery.py tests/test_api/test_oauth2_provider_api.py tests/test_api/test_settings_oauth2_endpoints.py tests/test_services/test_oauth2_provider_service.py -q
```

数据库迁移：

```bash
alembic upgrade head
alembic downgrade -1
```

代码检查：

```bash
ruff check .
```

## 相关文档

- [`README_ADMIN.md`](README_ADMIN.md)
- [`README_DEV.md`](README_DEV.md)
- [`CONFIG_GUIDE.md`](CONFIG_GUIDE.md)
- [`docs/version-upgrade-and-integration-guide.md`](docs/version-upgrade-and-integration-guide.md)
- `docs/df-superset-developer-integration-guide.md`

## 安全建议

- 生产环境必须使用 HTTPS
- `base_url` 必须配置为对外真实访问地址
- `oidc_issuer` 必须与下游实际使用的 issuer 保持一致
- 不要继续使用开发环境 RSA 密钥
- 严格限制 `ip_access.trusted_proxies`
- 根据实际域名限制 CORS
- 生产环境建议使用 PostgreSQL 或 MySQL，而不是默认 SQLite
- 对接方验签 `id_token` / `access_token` 时应校验 `iss`、`aud`、算法与过期时间

## 已知限制

- 当前更接近“基础可用版 OIDC Provider”，不是完整生产级 IdP
- 尚未提供完整的标准对外 revocation / introspection / logout 端点
- `userinfo` 中包含系统自定义字段，如 `roles`、`sso_roles`、`user_code`
- 开发环境首次运行需要手动准备 `settings.yaml` 与 RSA 密钥
- 当前仓库未提供 Dockerfile 与 GitHub Actions 工作流

## 贡献

欢迎提交 Issue 和 Pull Request。

建议流程：

1. Fork 仓库
2. 创建分支：`git checkout -b feature/your-feature`
3. 提交修改
4. 补充或更新测试
5. 发起 Pull Request

## 许可证

当前仓库尚未附带正式的 `LICENSE` 文件。

这表示当前仓库默认不向第三方授予复制、分发、修改或商用授权。

如果你计划将本项目以开源方式公开发布到 GitHub，请先补充实际采用的许可证文本，再在 README 中声明许可证类型。
