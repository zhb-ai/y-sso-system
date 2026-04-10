/**
 * 仪表盘页面 E2E 测试
 * 使用全局共享登录状态，避免并发登录冲突
 */
import { test, expect } from '@playwright/test';
import { navigateTo, ROUTES } from './fixtures/shared-auth.js';

test.describe.serial('仪表盘页面 - 元素存在性验证', () => {
  let page;

  test.beforeAll(async ({ browser }) => {
    // 使用已保存的登录状态创建上下文
    const context = await browser.newContext({
      storageState: 'playwright/.auth/user.json'
    });
    page = await context.newPage();

    // 直接导航到仪表盘
    console.log('[仪表盘] 开始测试...');
    await navigateTo(page, ROUTES.DASHBOARD);
    console.log('[仪表盘] 页面准备完成');
  });

  test.afterAll(async () => {
    // 清理：关闭页面
    if (page) {
      await page.context().close();
    }
  });

  test('页面标题和欢迎语显示正确', async () => {
    // 验证页面元素 - 使用更通用的选择器
    await expect(page.locator('.page-header h2')).toContainText('仪表盘');
    await expect(page.locator('.page-header h5')).toContainText('欢迎回来');
  });

  test('统计卡片存在', async () => {
    // 验证统计卡片
    await expect(page.locator('.stats-cards')).toBeVisible();
  });

  test('搜索区域元素存在', async () => {
    // 验证搜索区域元素
    await expect(page.locator('.filter-form')).toBeVisible();
  });

  test('登录记录表格和分页存在', async () => {
    // 验证表格和分页
    await expect(page.locator('.el-table')).toBeVisible();
    await expect(page.locator('.el-pagination')).toBeVisible();
  });
});
