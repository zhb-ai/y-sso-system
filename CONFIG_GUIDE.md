# SSO 系统配置指南

本文档说明 SSO 单点登录系统的配置文件 `config/settings.yaml` 中各参数的含义和用法。

> **注意**：本文档仅涵盖 SSO 项目实际使用到的配置项。底层 yweb 框架还提供了定时任务（`scheduler`）、文件存储（`storage`）等更多配置能力，详见 `yweb-core/docs/02_config_guide.md`。

## 配置原则

**不需要写全所有配置项。** `settings.yaml` 中只需写你要覆盖默认值的配置，未写的配置项会自动使用框架默认值。

### 必填配置（不写则系统无法正常运行）

| 配置项 | 原因 |
|--------|------|
| `database.url` | 框架默认为空字符串，不填则无法连接数据库 |

### 强烈建议填写（不填可运行但存在安全风险）

| 配置项 | 原因 |
|--------|------|
| `jwt.secret_key` | 框架默认为 `"change-me-in-production"`，不修改则任何人都能伪造 Token |

### 其他配置（均有合理默认值，按需覆盖即可）

其余所有配置项（日志、中间件、分页、Redis 等）均有合理的默认值，不写也能正常运行。只在需要调整时才写入 YAML。

**最小可运行配置示例：**

```yaml
database:
  url: sqlite:///./app/db/y_sso.db

jwt:
  secret_key: "your-secret-key-change-this-in-production"
```

仅这两项即可启动 SSO 系统，其余配置全部使用框架默认值。

---

## 配置文件位置

```
y-sso-system/
└── config/
    └── settings.yaml    # 主配置文件
```

## 配置项说明

### 1. 控制台日志配置

```yaml
enable_console_logging: true
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_console_logging` | bool | false | 是否启用控制台日志输出。开发环境建议设为 `true`，生产环境建议设为 `false` |

> 这是 SSO 项目自定义的顶层配置项（定义在 `app/config.py` 的 `Settings` 类中），不属于底层框架配置。

---

### 2. 数据库配置

```yaml
database:
  url: sqlite:///./app/db/y_sso.db
  echo: false
  pool_size: 5
  max_overflow: 10
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | string | （空） | 数据库连接 URL。支持 SQLite、PostgreSQL、MySQL |
| `echo` | bool | false | 是否打印 SQL 语句。调试用，生产环境建议关闭 |
| `pool_size` | int | 5 | 连接池大小（SQLite 不使用） |
| `max_overflow` | int | 10 | 连接池最大溢出数量（SQLite 不使用） |
| `pool_pre_ping` | bool | true | 连接前检查。防止数据库断连后使用失效连接 |
| `pool_timeout` | int | 30 | 获取连接超时时间（秒） |
| `pool_recycle` | int | 3600 | 连接回收时间（秒）。超过此时间的连接会被回收重建 |

> 环境变量前缀：`YWEB_DB_`（如 `YWEB_DB_URL`）

**数据库 URL 格式示例：**
- SQLite: `sqlite:///./app/db/y_sso.db`
- PostgreSQL: `postgresql://user:password@localhost:5432/dbname`
- MySQL: `mysql+pymysql://user:password@localhost:3306/dbname`

---

### 3. Redis 配置

```yaml
redis:
  url: redis://localhost:6379/0
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | string | （空） | Redis 连接地址 |
| `max_connections` | int | 10 | 最大连接数 |

> 环境变量前缀：`YWEB_REDIS_`（如 `YWEB_REDIS_URL`）

**Redis URL 格式：**
- 无密码: `redis://localhost:6379/0`
- 有密码: `redis://:password@localhost:6379/0`
- 使用 Unix Socket: `redis:///var/run/redis/redis.sock?db=0`

---

### 4. JWT 配置

```yaml
jwt:
  secret_key: "your-secret-key-change-this-in-production"
  algorithm: HS256
  access_token_expire_minutes: 30
  refresh_token_expire_days: 7
  refresh_token_sliding_days: 2
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `secret_key` | string | change-me-in-production | JWT 签名密钥。**生产环境必须修改** |
| `algorithm` | string | HS256 | JWT 签名算法 |
| `access_token_expire_minutes` | int | 30 | Access Token 有效期（分钟）。决定 Token 被盗后黑客最多能用多久 |
| `refresh_token_expire_days` | int | 7 | Refresh Token 基础有效期（天） |
| `refresh_token_sliding_days` | int | 2 | Refresh Token 滑动过期阈值（天）。当 Refresh Token 剩余时间少于此值时，会自动续期 |

**安全建议：**
- 生产环境务必修改 `secret_key`，使用随机生成的复杂字符串
- `access_token_expire_minutes` 不宜设置过长，建议 15-30 分钟
- `refresh_token_expire_days` 建议 7-30 天

---

### 5. 日志配置

```yaml
logging:
  level: DEBUG
  file_path: logs/app_{date}.log
  file_max_bytes: 10MB
  file_backup_count: 30
  file_encoding: utf-8
  file_when: midnight
  file_interval: 1
  enable_console: true
  max_retention_days: 0
  max_total_size: "0"
  sql_log_enabled: true
  sql_log_file_path: logs/sql_{date}.log
  sql_log_level: DEBUG
  sql_log_max_bytes: 50MB
  sql_log_backup_count: 10
```

> 环境变量前缀：`YWEB_LOG_`（如 `YWEB_LOG_LEVEL`）

#### 5.1 基础日志配置

| 参数 | 类型 | 框架默认值 | 说明 |
|------|------|--------|------|
| `level` | string | INFO | 日志级别。可选值: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `file_path` | string | logs/app_{date}.log | 日志文件路径。`{date}` 会被替换为日期 |
| `file_max_bytes` | string | 10MB | 单个日志文件最大大小。支持 B, KB, MB, GB, TB |
| `file_backup_count` | int | 30 | 保留的备份文件数量（同一天内的序号备份） |
| `file_encoding` | string | utf-8 | 日志文件编码 |
| `file_when` | string | midnight | 日志轮转时间点。可选值: midnight, S, M, H, D |
| `file_interval` | int | 1 | 日志轮转间隔 |
| `enable_console` | bool | true | 是否启用控制台输出（框架级开关） |
| `max_retention_days` | int | 0 | 日志保留天数。`0` 表示不限制，自动清理过期日志文件 |
| `max_total_size` | string | 0 | 日志文件总大小限制。`0` 表示不限制，支持 KB/MB/GB 单位 |

#### 5.2 SQL 日志配置（调试用）

| 参数 | 类型 | 框架默认值 | 说明 |
|------|------|--------|------|
| `sql_log_enabled` | bool | **false** | 是否启用 SQL 日志。开启后会将 SQLAlchemy 生成的 SQL 语句记录到单独的日志文件 |
| `sql_log_file_path` | string | logs/sql_{date}.log | SQL 日志文件路径 |
| `sql_log_level` | string | DEBUG | SQL 日志级别 |
| `sql_log_max_bytes` | string | 50MB | SQL 日志文件最大大小 |
| `sql_log_backup_count` | int | 10 | SQL 日志保留的备份文件数量 |

> **注意**：`sql_log_enabled` 在框架中默认为 `false`，SSO 项目在 `settings.yaml` 中手动设为 `true` 以便开发调试。

**生产环境建议：**
- 将 `level` 设为 `INFO` 或 `WARNING`
- 将 `sql_log_enabled` 设为 `false`
- 按需设置 `max_retention_days` 和 `max_total_size` 避免日志无限增长

---

### 6. 中间件配置

```yaml
middleware:
  request_log_max_body_size: 10KB
  request_log_skip_paths:
    - "/api/upload"
    - "/static/"
```

| 参数 | 类型 | 框架默认值 | 说明 |
|------|------|--------|------|
| `request_log_max_body_size` | string | 10KB | 请求体日志最大大小。超过此大小的请求体不会被完整记录 |
| `request_log_skip_paths` | list | ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"] | 跳过详细日志记录的路径列表 |
| `slow_request_threshold` | float | 1.0 | 慢请求阈值（秒）。超过此时间的请求会被标记为慢请求 |

> 环境变量前缀：`YWEB_MW_`

---

### 7. IP 访问控制配置

```yaml
ip_access:
  enabled: false
  default_policy: allow
  trusted_proxies:
    - "127.0.0.1"
  rules: []
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | bool | false | 是否启用 IP 访问控制。开发环境建议关闭，生产环境按需开启 |
| `default_policy` | string | allow | 默认策略。`allow` 表示放行，`deny` 表示拒绝 |
| `trusted_proxies` | list | ["127.0.0.1"] | 受信任代理 IP 列表。用于从 X-Forwarded-For 头提取真实 IP |
| `rules` | list | [] | IP 访问规则列表 |

**规则配置示例：**

```yaml
ip_access:
  enabled: true
  default_policy: deny
  trusted_proxies:
    - "127.0.0.1"
  rules:
    # 管理后台仅允许内网访问
    - paths: ["/api/v1/dashboard/*", "/api/v1/users/*", "/api/v1/roles/*"]
      allow_ips: ["192.168.0.0/16", "10.0.0.0/8"]
      description: "管理后台仅允许内网访问"
    # OAuth2 端点对外开放
    - paths: ["/api/v1/oauth2/*"]
      allow_ips: ["*"]
      description: "OAuth2 端点对外开放"
```

---

### 8. 分页配置

```yaml
pagination:
  max_page_size: 1000
  default_page_size: 10
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_page_size` | int | 1000 | 分页查询允许的最大页大小 |
| `default_page_size` | int | 10 | 默认每页数量 |

---

### 9. 基础 URL 配置

```yaml
base_url: "http://localhost:8000"
oidc_issuer: "http://localhost:8000/api/v1/oauth2"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `base_url` | string | http://localhost:8000 | 应用基础 URL。用于生成站点链接、回调地址等 |
| `oidc_issuer` | string\|null | null | OIDC Issuer。未配置时默认使用 `${base_url}/api/v1/oauth2` |

补充说明：

- `jwt_key_id` 用于生成 `JWKS` 中的 `kid`
- 如果当前安装的 `yweb` 版本较旧，`setup_auth()` 会自动忽略不兼容的 `key_id` 注入参数，避免启动失败

> 这是 SSO 项目自定义的顶层配置项（定义在 `app/config.py` 的 `Settings` 类中），不属于底层框架配置。

**生产环境示例：**
```yaml
base_url: "https://sso.yourcompany.com"
oidc_issuer: "https://sso.yourcompany.com/api/v1/oauth2"
```

---

## 环境变量覆盖

所有配置项均支持通过环境变量覆盖，环境变量名格式为：`<前缀><参数名>`，全部大写。

配置优先级（从高到低）：**环境变量 > YAML 配置文件 > 代码中的默认值**

**各模块的环境变量前缀：**

| 模块 | 前缀 | 示例 |
|------|------|------|
| 数据库 | `YWEB_DB_` | `YWEB_DB_URL` |
| Redis | `YWEB_REDIS_` | `YWEB_REDIS_URL` |
| JWT | `YWEB_JWT_` | `YWEB_JWT_SECRET_KEY` |
| 日志 | `YWEB_LOG_` | `YWEB_LOG_LEVEL` |
| 中间件 | `YWEB_MW_` | `YWEB_MW_SLOW_REQUEST_THRESHOLD` |
| 分页 | `YWEB_PAGE_` | `YWEB_PAGE_MAX_PAGE_SIZE` |

**SSO 项目常用环境变量示例：**

| 环境变量 | 对应配置 | 说明 |
|----------|----------|------|
| `YWEB_DB_URL` | `database.url` | 数据库连接 URL |
| `YWEB_JWT_SECRET_KEY` | `jwt.secret_key` | JWT 签名密钥 |
| `YWEB_JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `jwt.access_token_expire_minutes` | Access Token 有效期 |
| `YWEB_REDIS_URL` | `redis.url` | Redis 连接地址 |
| `YWEB_LOG_LEVEL` | `logging.level` | 日志级别 |

**使用示例：**
```bash
# 启动时通过环境变量覆盖 JWT 密钥
export YWEB_JWT_SECRET_KEY="my-super-secret-key"
python dev_server.py
```

```yaml
# docker-compose.yml 示例
environment:
  - YWEB_DB_URL=postgresql://user:pass@db:5432/sso_db
  - YWEB_JWT_SECRET_KEY=production-secret
  - YWEB_REDIS_URL=redis://redis:6379/0
  - YWEB_LOG_LEVEL=WARNING
```

---

## 生产环境配置建议

### 最小安全配置

```yaml
# 关闭控制台日志
enable_console_logging: false

# 使用强密码的数据库
database:
  url: postgresql://sso_user:strong_password@localhost:5432/sso_db
  echo: false

# 修改 JWT 密钥
jwt:
  secret_key: "your-random-generated-secret-key-at-least-32-chars"
  algorithm: HS256
  access_token_expire_minutes: 30
  refresh_token_expire_days: 7
  refresh_token_sliding_days: 2

# 调整日志级别
logging:
  level: INFO
  sql_log_enabled: false

# 启用 IP 访问控制（按需）
ip_access:
  enabled: true
  default_policy: allow
  rules:
    - paths: ["/api/v1/admin/*"]
      allow_ips: ["10.0.0.0/8"]

# 使用 HTTPS
base_url: "https://sso.yourcompany.com"
oidc_issuer: "https://sso.yourcompany.com/api/v1/oauth2"
```

---

## 配置文件重载

SSO 项目提供了 `reload_settings()` 函数（定义在 `app/config.py`）可重新加载配置文件。但需要注意：

**修改后需要重启服务才能生效的配置：**

- `database.*` — 数据库连接池在启动时创建，修改后必须重启
- `jwt.*` — JWT 密钥在启动时加载
- `redis.*` — Redis 连接在启动时建立

**修改后可通过 `reload_settings()` 重新加载的配置：**

- `logging.level` — 日志级别
- `ip_access.*` — IP 访问控制配置
- `pagination.*` — 分页配置
- `middleware.*` — 中间件配置

> 注意：`reload_settings()` 只重新读取 YAML 文件并更新 `settings` 对象，已初始化的组件（如数据库连接池）不会自动更新。

---

## 常见问题

### Q: 修改配置后没有生效？

A: 检查配置项是否支持热重载。不支持热重载的配置需要重启服务。

### Q: 如何查看当前生效的配置？

A: 可以在日志中查看启动时加载的配置，或通过 API 接口获取（需管理员权限）。

### Q: 配置文件格式错误怎么办？

A: 系统启动时会校验配置文件格式，如果格式错误会在控制台输出具体的错误信息。常见错误：
- YAML 缩进错误（必须使用空格，不能用 Tab）
- 缺少必需的冒号或引号
- 中文编码问题（确保文件使用 UTF-8 编码）

### Q: 敏感信息如何保护？

A: 建议使用环境变量覆盖敏感配置项（如 `jwt.secret_key`、`database.url`），避免将敏感信息写入配置文件。

---

## 缓存管理页面（管理员）

项目已接入缓存管理能力，管理员可在后台访问“缓存管理”页面进行运行时观测与运维操作。

### 访问入口

- 前端路由：`/cache`
- 后端前缀：`/api/v1/cache`
- 权限要求：管理员（`require_admin`）

### 可用功能

- 查看缓存函数列表（函数名、模块、后端、TTL、Key 前缀）
- 查看缓存统计（总命中/未命中、单函数统计）
- 清空单函数缓存或清空全部缓存
- 查看自动失效注册（模型 -> 函数 -> 事件）
- 启用/禁用自动失效
- 查看缓存条目预览（条目 key、剩余 TTL、类型、大小、脱敏值预览）

### 安全说明

- 缓存条目查看默认返回脱敏预览，不返回 raw 原始缓存值
- 常见敏感字段（如 `password`、`secret`、`token`）会自动掩码为 `***`
- 生产环境建议继续保留管理员权限限制，并配合审计日志
