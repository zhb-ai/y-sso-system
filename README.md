# 单点登录系统 (SSO System)

一个基于FastAPI和Vue.js的企业级单点登录系统，支持JWT认证、企业微信扫码登录、多应用管理、组织架构同步等功能。

## 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: SQLite (默认，轻量级部署)
- **ORM**: SQLAlchemy
- **认证**: JWT (JSON Web Token)
- **缓存**: Redis
- **第三方登录**: 企业微信
- **迁移工具**: Alembic

### 前端
- **框架**: Vue.js 3
- **构建工具**: Vite
- **状态管理**: Pinia
- **HTTP客户端**: Axios
- **UI组件库**: Element Plus

## 核心功能

1. **用户认证**
   - 用户名/密码登录
   - JWT令牌管理
   - 刷新令牌机制
   - 令牌过期自动处理

2. **第三方登录**
   - 企业微信扫码登录
   - 支持扩展其他第三方登录源

3. **多应用授权**
   - OAuth2.0授权码模式
   - 客户端凭证管理
   - 应用权限控制
   - 令牌颁发与撤销

4. **组织架构管理**
   - 企业微信组织架构同步
   - 部门管理（树形结构）
   - 员工管理
   - 同步记录追踪

5. **角色权限**
   - 基于角色的访问控制 (RBAC)
   - 动态权限分配
   - SSO角色管理

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 16+
- Redis 6.0+ (可选，用于缓存)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/your-repo/y-sso-system.git
   cd y-sso-system/y-sso-system
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **安装后端依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置文件**
   配置文件位于 `config/settings.yaml`，根据需要进行修改：
   ```bash
   # 主要配置项：
   # - database.url: 数据库连接地址
   # - jwt.secret_key: JWT密钥（生产环境必须修改）
   # - redis.url: Redis连接地址
   # - wechat.*: 企业微信配置
   ```

5. **初始化数据库**
   ```bash
   python init_db.py
   ```

6. **启动后端服务**

   **开发模式（推荐）**
   ```bash
   python dev_server.py
   ```

   **或使用 uvicorn 直接启动**
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **启动前端服务**

   **安装前端依赖（首次启动）**
   ```bash
   cd frontend
   npm install
   ```

   **启动开发服务器**
   ```bash
   npm run dev
   ```

8. **访问应用**
   - 管理后台: http://localhost:5200
   - 统一登录: http://localhost:5200/login
   - SSO门户: http://localhost:5200/sso/login
   - API文档: http://localhost:8000/docs
   - 健康检查: http://localhost:8000/health

## 配置说明

### 数据库配置
```yaml
database:
  url: sqlite:///./app/db/y_sso.db  # SQLite数据库文件路径
  echo: false  # 是否打印SQL语句
  pool_size: 5  # 连接池大小
  max_overflow: 10  # 连接池最大溢出数量
```

### Redis配置
```yaml
redis:
  url: redis://localhost:6379/0  # Redis连接地址
```

### JWT配置
```yaml
jwt:
  secret_key: "your-secret-key-change-this-in-production"  # JWT密钥
  algorithm: HS256  # JWT算法
  access_token_expire_minutes: 30  # 访问令牌过期时间（分钟）
  refresh_token_expire_days: 7  # 刷新令牌过期时间（天）
  refresh_token_sliding_days: 2  # 刷新令牌滑动过期阈值（天）
```

### 企业微信配置
```yaml
wechat:
  corp_id: "your-wechat-corp-id"  # 企业微信 Corp ID
  agent_id: "your-wechat-agent-id"  # 企业微信应用 ID
  secret: "your-wechat-secret"  # 企业微信应用 Secret
  redirect_uri: "http://localhost:8000/api/v1/wechat/callback"  # 回调地址
```

### 日志配置
```yaml
logging:
  level: DEBUG  # 日志级别
  file_path: logs/app_{date}.log  # 日志文件路径
  file_max_bytes: 10MB  # 单个日志文件最大大小
  file_backup_count: 30  # 日志文件备份数量
```

## API文档

### 认证相关
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/token` - 获取访问令牌
- `POST /api/v1/auth/refresh` - 刷新访问令牌
- `POST /api/v1/auth/logout` - 用户登出
- `POST /api/v1/auth/third-party/{source_type}` - 第三方登录

### 应用管理
- `GET /api/v1/applications` - 列出应用
- `POST /api/v1/applications` - 创建应用
- `GET /api/v1/applications/{app_id}` - 获取应用详情
- `PUT /api/v1/applications/{app_id}` - 更新应用
- `DELETE /api/v1/applications/{app_id}` - 删除应用

### 用户管理
- `GET /api/v1/users` - 列出用户
- `POST /api/v1/users` - 创建用户
- `GET /api/v1/users/{user_id}` - 获取用户详情
- `PUT /api/v1/users/{user_id}` - 更新用户
- `DELETE /api/v1/users/{user_id}` - 删除用户

### 角色管理
- `GET /api/v1/roles` - 列出角色
- `POST /api/v1/roles` - 创建角色
- `PUT /api/v1/roles/{role_id}` - 更新角色
- `DELETE /api/v1/roles/{role_id}` - 删除角色

### 组织架构
- `GET /api/v1/departments` - 列出部门
- `POST /api/v1/departments` - 创建部门
- `GET /api/v1/employees` - 列出员工
- `POST /api/v1/employees` - 创建员工

### 企业微信
- `GET /api/v1/wechat/login` - 企业微信登录
- `GET /api/v1/wechat/callback` - 企业微信登录回调
- `POST /api/v1/wechat/sync` - 同步企业微信组织架构

## 项目结构

```
y-sso-system/
├── app/                    # 后端应用代码
│   ├── api/               # API路由
│   │   ├── v1/           # API v1版本
│   │   ├── cors.py       # CORS配置
│   │   ├── dependencies.py # 依赖注入
│   │   ├── middleware.py  # 中间件
│   │   └── routes.py     # 路由注册
│   ├── domain/           # 领域层
│   │   ├── application/  # 应用领域
│   │   ├── auth/         # 认证领域
│   │   ├── config/       # 配置领域
│   │   ├── permission/   # 权限领域
│   │   ├── sso_role/     # SSO角色领域
│   │   └── wechat_work/  # 企业微信领域
│   ├── services/         # 应用服务层
│   ├── utils/            # 工具函数
│   ├── config.py         # 配置管理
│   ├── database.py       # 数据库连接
│   ├── main.py           # 应用入口
│   ├── models_registry.py # 模型注册
│   └── startup.py        # 启动脚本
├── config/               # 配置文件
│   └── settings.yaml     # 主配置文件
├── frontend/             # 前端代码
│   ├── src/             # 源代码
│   │   ├── api/        # API接口
│   │   ├── components/ # 组件
│   │   ├── layout/     # 布局
│   │   ├── pages/      # 页面
│   │   ├── router/     # 路由
│   │   ├── stores/     # 状态管理
│   │   └── styles/     # 样式
│   ├── package.json    # 依赖配置
│   └── vite.config.js  # Vite配置
├── tests/                # 测试代码
├── init_db.py           # 数据库初始化脚本
├── dev_server.py        # 开发服务器启动脚本
├── alembic.ini          # Alembic配置
└── requirements.txt      # 依赖列表
```

## 开发指南

### 运行测试
```bash
pytest
```

### 数据库迁移
```bash
# 创建迁移脚本
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 代码风格检查
```bash
ruff check .
```

### 生成依赖列表
```bash
pip freeze > requirements.txt
```

## 部署说明

### 开发环境
使用 `dev_server.py` 启动：
```bash
python dev_server.py
```

### 生产环境
建议使用 `gunicorn` + `uvicorn` 部署：
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

## 安全建议

1. **生产环境配置**
   - 修改 JWT secret_key
   - 使用 HTTPS
   - 限制 CORS 来源
   - 定期轮换密钥

2. **数据库安全**
   - 生产环境建议使用 PostgreSQL 或 MySQL
   - 配置强密码
   - 限制数据库访问 IP

3. **日志安全**
   - 避免记录敏感信息
   - 配置适当的日志级别
   - 定期清理日志文件

4. **IP访问控制**
   - 可在 `config/settings.yaml` 中启用 IP 访问控制
   - 配置允许访问的 IP 地址段

## 扩展开发

### 添加新的认证源
1. 继承 `AuthenticationSource` 抽象类
2. 实现必要的方法
3. 在 `AuthApplicationService` 中注册

### 添加新的组织同步源
1. 继承 `OrganizationSyncSource` 抽象类
2. 实现必要的方法
3. 在 `OrganizationSyncServiceImpl` 中注册

## 相关文档

- [管理员使用指南](README_ADMIN.md) - 系统安装、启动、功能模块说明
- [开发服务器启动说明](README_DEV.md) - 开发环境启动和调试说明
- [配置指南](CONFIG_GUIDE.md) - 配置文件详细说明

## 许可证

MIT License

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 联系方式

如有问题或建议，欢迎联系：
- 邮件: your-email@example.com
- GitHub: [your-github-username](https://github.com/your-github-username)
