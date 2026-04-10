/**
 * 单点登录页面 E2E 测试
 * 注意：登录页面测试不使用全局登录状态
 */
import { test, expect } from '@playwright/test';
import { login } from './fixtures/auth.js';
import { ROUTES, getFullUrl } from './fixtures/test-config.js';

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
    await page.waitForTimeout(2000);

    // 验证显示用户信息 - 使用更通用的选择器
    await expect(page.locator('.sso-username, .sso-user-info, .sso-user-detail').first()).toBeVisible();

    await context.close();
  });

  test('已登录时显示进入管理后台链接', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    // 先登录
    await login(page);

    // 访问SSO登录页
    await page.goto(getFullUrl(ROUTES.SSO_LOGIN));
    await page.waitForTimeout(2000);

    // 验证显示"进入管理后台"链接
    await expect(page.locator('a:has-text("进入管理后台")')).toBeVisible();

    await context.close();
  });
});
