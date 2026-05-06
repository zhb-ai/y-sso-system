/**
 * token 失效/缺失时的鉴权兜底用例
 * 验证 smart-auth.js 的登录重试与受保护路由恢复能力
 */
import { test, expect } from '@playwright/test';
import { smartNavigate } from './fixtures/smart-auth.js';
import { ROUTES } from './fixtures/test-config.js';

test.describe.serial('鉴权边界 - token 失效兜底', () => {
  test('清空 token 后 smartNavigate 能重登并恢复访问', async ({ browser }) => {
    const context = await browser.newContext({
      storageState: 'playwright/.auth/user.json',
    });
    const page = await context.newPage();

    // 先进入一个受保护页面，确保初始 token/用户信息存在
    await smartNavigate(page, ROUTES.DASHBOARD, { checkAuth: true });
    await expect(page.locator('h2').first()).toContainText('仪表盘');

    // 清空 token / userInfo，模拟 token 失效
    await page.evaluate(() => {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userInfo');
      sessionStorage.removeItem('token');
      sessionStorage.removeItem('userInfo');
    });

    // 监听是否会重定向到登录页（重登兜底的关键证据）
    const loginVisited = page
      .waitForURL('**/login', { timeout: 10000 })
      .then(() => true)
      .catch(() => false);

    // 再次访问另一个受保护页面
    await smartNavigate(page, ROUTES.ROLES, { checkAuth: true });

    expect(await loginVisited).toBe(true);
    await expect(page.locator('h2').first()).toContainText('角色管理');

    await context.close();
  });
});

