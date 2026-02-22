# 单点登录系统 - 管理员使用指南

## 一、登录地址

### 统一登录页面
- **地址**：http://localhost:5200/login
- **用途**：管理员登录系统管理后台，进行应用管理、用户管理、系统设置等操作

### 单点登录门户
- **地址**：http://localhost:5200/sso/login
- **用途**：普通用户登录单点登录系统，获取访问令牌

## 二、初始管理员账号

系统初始化时会自动创建一个管理员账号：

| 用户名 | 密码     | 邮箱                | 角色   |
|--------|----------|---------------------|--------|
| admin  | admin123 | admin@example.com   | 管理员 |

## 三、系统初始化过程

### 1. 数据库初始化

系统提供了 `init_db.py` 脚本用于初始化数据库，包括：

- 创建所有数据库表
- 创建管理员角色、内部员工角色、外部用户角色
- 创建初始管理员账号
- 给管理员账号分配管理员角色

**执行方式**：
```bash
cd y-sso-system
python init_db.py
```

### 2. 数据库位置

数据库文件存放在 `app/db` 目录下：
- **数据库文件**：`app/db/y_sso.db`
- **数据库类型**：SQLite

## 四、系统启动步骤

### 1. 启动后端服务

#### 方式一：开发模式（推荐开发时使用）
使用 dev_server.py 启动，支持自动重载、调试模式等开发特性：

```bash
cd y-sso-system
python dev_server.py
```

#### 方式二：生产模式 - Uvicorn 直接启动
```bash
cd y-sso-system
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```



后端服务启动成功后，可以访问 API 文档：
- **API 文档地址**：http://localhost:8000/docs
- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc

### 2. 启动前端服务

#### 开发模式（首次启动需先安装依赖）

**第一步：安装依赖（首次启动时执行）**
```bash
cd y-sso-system/frontend
npm install
```

**第二步：启动开发服务器**
```bash
npm run dev
```

#### 生产模式（已打包的项目）
如果前端已经打包完成（`dist` 目录存在），可以直接使用 preview 模式：
```bash
cd y-sso-system/frontend
npm run preview
```

前端服务启动成功后，可以访问：
- **管理后台**：http://localhost:5200
- **统一登录**：http://localhost:5200/login
- **SSO 门户**：http://localhost:5200/sso/login

## 五、功能模块

### 1. 应用管理
- 查看应用列表
- 创建新应用
- 编辑应用信息
- 启用/禁用应用
- 重置应用密钥

### 2. 用户管理
- 查看用户列表
- 创建新用户
- 编辑用户信息
- 启用/禁用用户
- 重置用户密码
- 分配用户角色

### 3. 角色权限管理
- 查看角色列表
- 创建新角色
- 编辑角色信息
- 删除角色
- 分配角色权限

### 4. SSO 角色管理
- 查看 SSO 角色列表
- 创建 SSO 角色
- 编辑 SSO 角色信息
- 删除 SSO 角色

### 5. 组织架构管理
- 部门管理（支持树形结构）
- 员工管理
- 企业微信组织架构同步

### 6. 系统设置
- JWT 配置
- 企业微信配置
- 基本设置
- 日志设置

### 7. 个人资料
- 查看个人信息
- 修改密码

## 六、系统配置

### 配置文件位置
- **配置文件**：`config/settings.yaml`

### 配置文档
详细的配置说明请参考：[配置指南](CONFIG_GUIDE.md)

### 主要配置项
- **数据库配置**：`database.url`
- **JWT 配置**：`jwt.*`
- **企业微信配置**：`wechat.*`
- **日志配置**：`logging.*`
- **Redis 配置**：`redis.*`
- **IP 访问控制**：`ip_access.*`

## 七、注意事项

1. 生产环境中请修改初始管理员密码
2. 定期备份数据库文件
3. 生产环境中请关闭调试模式（`enable_console_logging: false`）
4. 生产环境中请配置合适的 JWT 密钥和过期时间
5. 生产环境中请配置合适的日志级别和日志文件路径
6. 如需启用 IP 访问控制，请修改 `ip_access.enabled` 为 `true`

## 八、故障排查

### 1. 数据库连接失败
- 检查数据库文件路径是否正确
- 检查数据库文件权限
- 确保数据库目录存在

### 2. 登录失败
- 检查用户名和密码是否正确
- 检查用户是否被禁用
- 检查数据库中是否存在该用户
- 检查 JWT 配置是否正确

### 3. 前端页面无法访问
- 检查前端服务是否启动
- 检查端口 5200 是否被占用
- 检查浏览器缓存

### 4. 后端服务无法启动
- 检查依赖是否安装完整（`pip install -r requirements.txt`）
- 检查端口 8000 是否被占用
- 检查配置文件是否正确
- 检查 Redis 是否已启动（如启用 Redis）

### 5. 企业微信同步失败
- 检查企业微信配置是否正确
- 检查网络连接
- 查看日志文件获取详细错误信息

## 九、技术栈

### 后端
- Python 3.11+
- FastAPI
- SQLAlchemy
- JWT
- SQLite
- Redis
- Alembic（数据库迁移）

### 前端
- Vue 3
- Element Plus
- Pinia
- Vue Router
- Axios
- Vite

## 十、目录结构

```
y-sso-system/
├── app/                    # 后端应用代码
│   ├── api/               # API 路由
│   ├── domain/            # 领域层
│   ├── services/          # 应用服务层
│   ├── utils/             # 工具函数
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   ├── main.py            # 应用入口
│   └── models_registry.py # 模型注册
├── config/                # 配置文件
│   └── settings.yaml      # 主配置文件
├── frontend/              # 前端代码
│   ├── src/              # 源代码
│   │   ├── api/          # API 接口
│   │   ├── components/   # 组件
│   │   ├── layout/       # 布局
│   │   ├── pages/        # 页面
│   │   ├── router/       # 路由
│   │   ├── stores/       # 状态管理
│   │   └── styles/       # 样式
│   ├── package.json      # 依赖配置
│   └── vite.config.js    # Vite 配置
├── tests/                 # 测试代码
├── init_db.py            # 数据库初始化脚本
├── dev_server.py         # 开发服务器启动脚本
└── alembic.ini           # Alembic 配置
```

## 十一、联系信息

如有问题，请联系系统管理员。
