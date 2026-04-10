/**
 * 登录页面 E2E 测试
 * 注意：登录页面测试不使用全局登录状态
 */
import { test, expect } from '@playwright/test';
import { ROUTES, getFullUrl } from './fixtures/test-config.js';

test.describe.serial('登录页面 - 元素存在性验证', () => {

  test('页面标题存在', async ({ browser }) => {
    // 创建无登录状态的上下文
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    await page.goto(getFullUrl(ROUTES.LOGIN));

    // 验证页面标题
    await expect(page.locator('.login-header h1')).toBeVisible();

    await context.close();
  });

  test('用户名输入框存在', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    await page.goto(getFullUrl(ROUTES.LOGIN));

    // 验证用户名输入框
    await expect(page.locator('.login-form input[placeholder="用户名"]')).toBeVisible();

    await context.close();
  });

  test('密码输入框存在', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    await page.goto(getFullUrl(ROUTES.LOGIN));

    // 验证密码输入框
    await expect(page.locator('.login-form input[type="password"]')).toBeVisible();

    await context.close();
  });

  test('登录按钮存在', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    await page.goto(getFullUrl(ROUTES.LOGIN));

    // 验证登录按钮
    await expect(page.locator('.login-form button:has-text("登录")')).toBeVisible();

    await context.close();
  });

  test('记住密码复选框存在', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    await page.goto(getFullUrl(ROUTES.LOGIN));

    // 验证记住密码复选框
    await expect(page.locator('.el-checkbox')).toBeVisible();

    await context.close();
  });

  test('忘记密码链接存在', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    await page.goto(getFullUrl(ROUTES.LOGIN));

    // 验证忘记密码链接
    await expect(page.locator('a:has-text("忘记密码")')).toBeVisible();

    await context.close();
  });
});
