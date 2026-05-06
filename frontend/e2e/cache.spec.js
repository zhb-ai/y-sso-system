/**
 * 缓存管理页面 E2E 测试
 * 优化：直接访问缓存管理页面，如果token不存在或失效则自动登录
 */
import { test, expect, smartNavigate } from './fixtures/smart-test-base.js';
import { ROUTES } from './fixtures/test-config.js';

test.describe.serial('缓存管理页面 - 元素存在性验证', () => {
  let page;
  let context;

  test.beforeAll(async ({ browser }) => {
    // 创建新的浏览器上下文
    context = await browser.newContext();
    page = await context.newPage();

    // 直接访问缓存管理页面，smartNavigate会自动处理登录
    console.log('[缓存管理] 开始测试，直接访问页面...');
    await smartNavigate(page, ROUTES.CACHE, { checkAuth: true });
    console.log('[缓存管理] 页面准备完成');
  });

  test.afterAll(async () => {
    // 清理：关闭上下文
    if (context) {
      await context.close();
    }
  });

  test('页面标题存在', async () => {
    // 验证页面标题 - 使用更通用的选择器
    await expect(page.locator('h2').first()).toContainText('缓存');
  });

  test('操作按钮存在', async () => {
    // 验证操作按钮
    await expect(page.getByRole('button', { name: '刷新' })).toBeVisible();
  });

  test('缓存统计区域存在', async () => {
    // 验证缓存统计区域
    await expect(page.locator('.el-card').first()).toBeVisible();
  });

  test('缓存表格存在', async () => {
    // 验证缓存表格
    await expect(page.locator('.el-table')).toBeVisible();
  });

  test('打开缓存条目抽屉并展示内容', async () => {
    const functionRow = page.locator('.data-card .el-table__row').first();
    await expect(functionRow).toBeVisible({ timeout: 10000 });

    // 打开“条目”抽屉
    await functionRow.locator('button:has-text("条目")').first().click();

    const drawerHeader = page.locator('.el-drawer__header');
    await expect(drawerHeader).toBeVisible({ timeout: 10000 });
    await expect(drawerHeader).toContainText('缓存条目');

    const emptyState = page.getByText('请选择缓存条目');
    const entryRows = page.locator('.drawer-content .el-table__row');

    // 等待“条目列表”或“空状态”二选一出现，证明抽屉确实加载完成
    const result = await Promise.race([
      entryRows.first().waitFor({ state: 'visible', timeout: 10000 }).then(() => 'rows').catch(() => null),
      emptyState.waitFor({ state: 'visible', timeout: 10000 }).then(() => 'empty').catch(() => null),
    ]);

    expect(result).not.toBeNull();
  });
});
