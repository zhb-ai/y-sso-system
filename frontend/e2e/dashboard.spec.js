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

  test('搜索后展示空态或结果，并可重置', async () => {
    const searchInput = page.locator('.filter-form input[placeholder="请输入用户名"]').first();
    await searchInput.waitFor({ state: 'visible', timeout: 10000 });

    // 使用一个几乎不可能命中的随机用户名，验证搜索结果链路
    const keyword = `e2e_no_user_${Math.random().toString(36).slice(2, 10)}`;
    await searchInput.fill(keyword);
    await page.locator('.filter-form button:has-text("搜索")').click();

    const emptyTitle = page.getByText('暂无登录记录');
    const rows = page.locator('.login-record-card .el-table__row');
    await expect.poll(async () => {
      const emptyVisible = await emptyTitle.isVisible().catch(() => false);
      const rowCount = await rows.count();
      return emptyVisible || rowCount > 0;
    }).toBe(true);

    await page.locator('.filter-form button:has-text("重置")').click();
    await expect(searchInput).toHaveValue('');

    // 重置后至少应能看到空态或表格行
    const resetEmpty = page.getByText('暂无登录记录');
    const resetRows = page.locator('.login-record-card .el-table__row');
    await expect.poll(async () => {
      const emptyVisible = await resetEmpty.isVisible().catch(() => false);
      const rowCount = await resetRows.count();
      return emptyVisible || rowCount > 0;
    }).toBe(true);
  });

  test('登录记录表格和分页存在', async () => {
    // 验证表格和分页
    await expect(page.locator('.el-table')).toBeVisible();
    await expect(page.locator('.el-pagination')).toBeVisible();
  });
});
