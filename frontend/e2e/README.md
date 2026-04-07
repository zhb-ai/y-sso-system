# Y-SSO 系统 E2E 测试

本项目使用 [Playwright](https://playwright.dev/) 进行端到端测试。

## 测试账号配置

所有需要登录的测试使用以下默认测试账号：

- **用户名**: `admin`
- **密码**: `admin123`

账号配置位于 `e2e/fixtures/auth.js` 中的 `TEST_CREDENTIALS` 常量。

## 测试特点

### 显式登录流程

**每个需要登录的测试都会独立执行完整的登录流程**：

1. 访问登录页面 `/login`
2. 输入用户名 `admin`
3. 输入密码 `admin123`
4. 点击登录按钮
5. 等待跳转到仪表盘 `/dashboard`
6. 验证登录成功
7. 导航到目标测试页面
8. 验证页面元素

这样可以确保：
- 每个测试都是独立的
- 登录状态正确
- 页面数据正常加载

## 目录结构

```
e2e/
├── fixtures/           # 测试 fixtures
│   └── auth.js        # 认证相关的 fixtures，提供 performLogin 函数
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

## 测试覆盖页面

| 页面 | 测试文件 | 登录方式 |
|------|----------|----------|
| 登录页 | `login.spec.js` | 无需登录 |
| 单点登录页 | `sso-login.spec.js` | 无需登录 |
| 仪表盘 | `dashboard.spec.js` | 显式登录 |
| 应用管理 | `applications.spec.js` | 显式登录 |
| 用户管理 | `users.spec.js` | 显式登录 |
| 角色管理 | `roles.spec.js` | 显式登录 |
| SSO角色 | `sso-roles.spec.js` | 显式登录 |
| 组织架构 | `organization.spec.js` | 显式登录 |
| 员工管理 | `employees.spec.js` | 显式登录 |
| 系统设置 | `settings.spec.js` | 显式登录 |
| 缓存管理 | `cache.spec.js` | 显式登录 |

## 快速开始

### 1. 安装浏览器

```bash
npm run test:install
```

### 2. 运行测试

```bash
# 运行所有测试
npm run test

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

### 测试类型

所有测试都是**简单的元素存在性验证**，不做功能测试：

- 验证页面标题是否存在
- 验证输入框是否存在
- 验证按钮是否存在
- 验证表格是否存在
- 验证分页组件是否存在

### 显式登录示例

```javascript
import { test, expect, performLogin } from './fixtures/auth.js';
import { DashboardPage } from './pages/DashboardPage.js';

test('仪表盘页面测试', async ({ page }) => {
  // 显式执行登录流程（访问登录页 -> 输入账号密码 -> 点击登录 -> 验证成功）
  await performLogin(page);
  
  // 登录成功后，导航到目标页面
  const dashboardPage = new DashboardPage(page);
  await dashboardPage.goto();
  await dashboardPage.expectPageLoaded();
  
  // 验证页面元素
  await expect(dashboardPage.pageTitle).toBeVisible();
});
```

### 测试账号

默认测试账号：
- 用户名：`admin`
- 密码：`admin123`

如需修改，请编辑 `e2e/fixtures/auth.js` 文件中的 `TEST_CREDENTIALS` 常量。
