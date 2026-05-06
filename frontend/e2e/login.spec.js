/**
 * 登录页面 E2E 测试
 * 注意：登录页面测试不使用全局登录状态
 */
import { test, expect } from '@playwright/test';
import { ROUTES, getFullUrl } from './fixtures/test-config.js';

test.use({ storageState: undefined });

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

test.describe.serial('登录页面 - 登录成功/失败断言', () => {
  test('登录成功后进入 SSO 登录页并展示用户信息', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    await page.goto(getFullUrl(ROUTES.LOGIN));

    await page.locator('.login-form input[placeholder="用户名"]').fill('admin');
    await page.locator('.login-form input[type="password"]').fill('admin123');
    await page.locator('.login-form button:has-text("登录")').click();

    // 登录页成功后会跳转到 SSO 门户页（router.push("/sso/login")）
    await expect(page).toHaveURL(/\/sso\/login/);

    const ssoUserInfo = page.locator('.sso-username, .sso-user-info, .sso-user-detail').first();
    await expect(ssoUserInfo).toBeVisible({ timeout: 10000 });

    await context.close();
  });

  test('登录失败时展示错误提示并保持在登录页', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined });
    const page = await context.newPage();

    await page.goto(getFullUrl(ROUTES.LOGIN));

    await page.locator('.login-form input[placeholder="用户名"]').fill('admin');
    await page.locator('.login-form input[type="password"]').fill('wrong_password');
    await page.locator('.login-form button:has-text("登录")').click();

    const errorMsg = page.locator('.el-message--error, .el-form-item__error').first();
    await expect(errorMsg).toBeVisible({ timeout: 5000 });

    const text = (await errorMsg.innerText()).trim();
    expect(text).toMatch(/用户名或密码错误|登录失败/);

    await expect(page).toHaveURL(/\/login/);

    await context.close();
  });
});
