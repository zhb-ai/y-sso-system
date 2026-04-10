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
});
