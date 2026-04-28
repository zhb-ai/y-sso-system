# Y-SSO 系统 E2E 测试

本项目使用 [Playwright](https://playwright.dev/) 进行真实后端联调的端到端测试。

## 当前测试策略

### 1. 统一认证基座

默认使用 `playwright.config.js` 中的 `globalSetup` 先生成共享登录态，再通过 `storageState` 复用到大多数后台测试。

- 共享登录态文件：`playwright/.auth/user.json`
- 主认证逻辑：`e2e/fixtures/smart-auth.js`
- 全局登录入口：`e2e/fixtures/global-setup.js`

登录成功的判定不再依赖页面文案，而是基于：

1. token / `userInfo` 已写入浏览器存储
2. 已进入受保护页面或 SSO 门户页
3. 测试账号满足后台访问前置条件（默认要求 `admin` 角色）

### 2. 公共页面与后台页面分离

- `login.spec.js`、`sso-login.spec.js` 属于公共页面测试，不复用登录态
- 其余后台页面测试默认复用共享登录态

### 3. Smoke 与 Stateful 分层

- `npm run test:smoke`：登录、SSO 门户、仪表盘、系统设置、缓存等稳定页面验证
- `npm run test:stateful`：应用、用户、角色、组织、员工、个人资料等带数据变更的联调用例

## 目录结构

```
e2e/
├── fixtures/           # 测试 fixtures
│   ├── global-setup.js # 全局登录，生成共享 storageState
│   ├── smart-auth.js   # 统一登录 / 校验 / 导航能力
│   ├── shared-auth.js  # 基于共享登录态的后台导航
│   └── auth.js         # 兼容层，复用 smart-auth
├── pages/             # Page Object Models
│   ├── BasePage.js    # 基础页面对象
│   ├── LoginPage.js   # 登录页面对象
│   ├── SSOLoginPage.js # 单点登录页面对象
│   ├── DashboardPage.js # 仪表盘页面对象
│   ├── ApplicationsPage.js # 应用管理页面对象
│   ├── UsersPage.js   # 用户管理页面对象
│   ├── RolesPage.js   # 角色管理页面对象
│   ├── SSORolesPage.js # SSO角色页面对象
│   ├── OrganizationPage.js # 组织架构页面对象
│   ├── EmployeesPage.js # 员工管理页面对象
│   ├── SettingsPage.js # 系统设置页面对象
│   └── CachePage.js   # 缓存管理页面对象
├── login.spec.js      # 登录页面测试（无需登录）
├── sso-login.spec.js  # 单点登录页面测试（无需登录）
├── dashboard.spec.js  # 仪表盘页面测试（显式登录）
├── applications.spec.js # 应用管理测试（显式登录）
├── users.spec.js      # 用户管理测试（显式登录）
├── roles.spec.js      # 角色管理测试（显式登录）
├── sso-roles.spec.js  # SSO角色测试（显式登录）
├── organization.spec.js # 组织架构测试（显式登录）
├── employees.spec.js  # 员工管理测试（显式登录）
├── settings.spec.js   # 系统设置测试（显式登录）
└── cache.spec.js      # 缓存管理测试（显式登录）
```

## 环境变量

可选环境变量如下：

- `PLAYWRIGHT_BASE_URL`：前端地址，默认 `http://localhost:5200`
- `E2E_USERNAME`：测试账号用户名，默认 `admin`
- `E2E_PASSWORD`：测试账号密码，默认 `admin123`
- `PLAYWRIGHT_AUTH_FILE`：共享登录态文件路径
- `E2E_REQUIRE_ADMIN`：是否要求测试账号具备 `admin` 角色，默认 `true`

## 环境前置条件

运行后台联调测试前，请确保：

1. 前端可在 `PLAYWRIGHT_BASE_URL` 正常访问
2. 后端接口可用，登录接口与受保护页面可联通
3. 测试账号不是“首次登录必须改密”状态
4. 若运行后台测试，测试账号具备 `admin` 角色

## 快速开始

### 1. 安装浏览器

```bash
npm run test:install
```

### 2. 运行测试

```bash
# 运行所有测试
npm run test

# 运行稳定 smoke 套件
npm run test:smoke

# 运行带数据变更的 stateful 套件
npm run test:stateful

# 运行特定测试文件
npx playwright test login.spec.js
npx playwright test dashboard.spec.js

# 可视化模式（可以看到浏览器界面）
npm run test:headed

# UI 模式（交互式调试）
npm run test:ui

# 调试模式
npm run test:debug
```

### 3. 查看测试报告

```bash
npm run test:report
```

## 测试说明

- smoke 套件以页面加载和关键元素可见为主，用于快速验证登录链路和核心页面可用性
- stateful 套件包含新建、编辑、删除等操作，对测试数据与账号权限更敏感
- 若全局登录失败，优先检查测试账号权限、是否触发强制改密，以及后端接口是否正常
