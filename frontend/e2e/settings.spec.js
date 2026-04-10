/**
 * 系统设置页面 E2E 测试
 * 优化：直接访问系统设置页面，如果token不存在或失效则自动登录
 */
import { test, expect, smartNavigate } from './fixtures/smart-test-base.js';
import { ROUTES } from './fixtures/test-config.js';

test.describe.serial('系统设置页面 - 元素存在性验证', () => {
  let page;
  let context;

  test.beforeAll(async ({ browser }) => {
    // 创建新的浏览器上下文
    context = await browser.newContext();
    page = await context.newPage();

    // 直接访问系统设置页面，smartNavigate会自动处理登录
    console.log('[系统设置] 开始测试，直接访问页面...');
    await smartNavigate(page, ROUTES.SETTINGS, { checkAuth: true });
    console.log('[系统设置] 页面准备完成');
  });

  test.afterAll(async () => {
    // 清理：关闭上下文
    if (context) {
      await context.close();
    }
  });

  test('页面标题存在', async () => {
    // 验证页面标题
    await expect(page.locator('.page-header h2')).toContainText('系统设置');
  });

  test('设置卡片和表单存在', async () => {
    // 验证设置卡片和表单
    await expect(page.locator('.el-card').first()).toBeVisible();
    await expect(page.locator('.el-form').first()).toBeVisible();
  });

  test('保存按钮存在', async () => {
    // 验证保存按钮
    await expect(page.getByRole('button', { name: '保存' })).toBeVisible();
  });
});
