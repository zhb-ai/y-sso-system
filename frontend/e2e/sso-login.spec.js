/**
 * 单点登录页面 E2E 测试
 * 注意：登录页面测试不使用全局登录状态
 */
import { test, expect } from '@playwright/test';
import { login } from './fixtures/auth.js';
import { ROUTES, getFullUrl } from './fixtures/test-config.js';

test.use({ storageState: undefined });

test.describe.serial('单点登录页面 - 元素存在性验证', () => {

  test('页面标题存在', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    await page.goto(getFullUrl(ROUTES.SSO_LOGIN));

    // 验证页面标题
    await expect(page.locator('.login-header h1')).toBeVisible();

    await context.close();
  });

  test('用户名输入框存在', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    await page.goto(getFullUrl(ROUTES.SSO_LOGIN));

    // 验证用户名输入框
    await expect(page.locator('.login-form input[placeholder*="用户名"]')).toBeVisible();

    await context.close();
  });

  test('密码输入框存在', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    await page.goto(getFullUrl(ROUTES.SSO_LOGIN));

    // 验证密码输入框
    await expect(page.locator('.login-form input[type="password"]')).toBeVisible();

    await context.close();
  });

  test('登录按钮存在', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    await page.goto(getFullUrl(ROUTES.SSO_LOGIN));

    // 验证登录按钮 - 使用更通用的选择器
    await expect(page.locator('.login-form button').first()).toBeVisible();

    await context.close();
  });

  test('已登录时显示用户信息', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    // 先登录
    await login(page);

    // 访问SSO登录页
    await page.goto(getFullUrl(ROUTES.SSO_LOGIN));

    // 验证显示用户信息 - 使用更通用的选择器
    await expect(page.locator('.sso-username, .sso-user-info, .sso-user-detail').first()).toBeVisible();

    await context.close();
  });

  test('已登录时显示管理后台链接', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    // 先登录
    await login(page);

    // 访问SSO登录页
    await page.goto(getFullUrl(ROUTES.SSO_LOGIN));

    // 验证显示"管理后台"链接
    await expect(page.locator('a:has-text("管理后台")')).toBeVisible();

    await context.close();
  });
});

test.describe.serial('单点登录页面 - 登录失败断言', () => {
  test('登录失败时展示错误提示并保持在 SSO 登录页', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    await page.goto(getFullUrl(ROUTES.SSO_LOGIN));

    await page.locator('.login-form input[placeholder*="用户名"]').first().fill('admin');
    await page.locator('.login-form input[type="password"]').first().fill('wrong_password');

    const loginBtn = page.locator('.login-form button:has-text("登录")').first();
    await expect(loginBtn).toBeVisible({ timeout: 5000 });
    await loginBtn.click();

    const errorMsg = page.locator('.el-message--error, .el-form-item__error').first();
    await expect(errorMsg).toBeVisible({ timeout: 5000 });

    const text = (await errorMsg.innerText()).trim();
    expect(text).toMatch(/登录失败|用户名或密码错误/);

    await expect(page).toHaveURL(/\/sso\/login/);

    await context.close();
  });
});
