/**
 * 应用管理页面 E2E 测试
 * 优化：使用 test.describe.serial 只登录一次，所有测试共享登录状态
 */
import { test, expect } from './fixtures/test-base.js';
import { navigateToPage } from './fixtures/test-base.js';
import { generateAppData, generateAppName } from './fixtures/test-data.js';

test.describe.serial('应用管理页面 - 完整测试流程', () => {
  // 存储测试过程中创建的应用信息
  let createdApp = null;
  let updatedAppName = null;
  let page;

  test.beforeAll(async ({ browser }) => {
    // 在所有测试开始前登录
    const context = await browser.newContext();
    page = await context.newPage();
    
    // 执行登录 - 使用与 auth.js 相同的逻辑
    await page.goto('http://localhost:5200/login');
    await page.waitForLoadState('networkidle');
    
    // 输入用户名
    const usernameInput = page.locator('.login-form input[placeholder="用户名"]').first();
    await usernameInput.waitFor({ timeout: 10000 });
    await usernameInput.fill('admin');
    
    // 输入密码
    const passwordInput = page.locator('.login-form input[placeholder="密码"]').first();
    await passwordInput.fill('admin123');
    
    // 点击登录按钮
    await page.locator('.login-form button:has-text("登录")').click();
    
    // 等待跳转到SSO登录页或仪表盘
    await page.waitForTimeout(3000);
    
    // 检查当前URL
    const currentUrl = page.url();
    
    // 如果跳转到sso/login，需要点击"进入管理后台"
    if (currentUrl.includes('/sso/login')) {
      await page.locator('a').filter({ hasText: '进入管理后台' }).waitFor({ timeout: 10000 });
      await page.locator('a').filter({ hasText: '进入管理后台' }).click();
      await page.waitForTimeout(2000);
    }
    
    // 检查是否登录成功
    const finalUrl = page.url();
    if (finalUrl.includes('/login')) {
      throw new Error('登录失败，仍在登录页面');
    }
  });

  test.afterAll(async () => {
    // 所有测试结束后关闭页面
    if (page) {
      await page.close();
    }
  });

  test('1. 页面元素验证', async () => {
    // 导航到应用管理页面
    await navigateToPage(page, '应用管理');

    // 验证页面标题
    await expect(page.locator('h2').first()).toContainText('应用管理');

    // 验证搜索区域
    await expect(page.locator('.filter-form')).toBeVisible();

    // 验证表格
    await expect(page.locator('.el-table')).toBeVisible();
    await page.waitForSelector('.el-table__row', { timeout: 10000 });

    // 验证操作按钮
    await expect(page.locator('button:has-text("编辑")').first()).toBeVisible();
    await expect(page.locator('button:has-text("删除")').first()).toBeVisible();
    await expect(page.locator('button:has-text("密钥")').first()).toBeVisible();
    await expect(page.locator('button:has-text("新建")').first()).toBeVisible();
  });

  test('2. 新建应用', async () => {
    // 生成随机应用数据
    createdApp = generateAppData();

    // 点击新建按钮
    await page.locator('button:has-text("新建")').first().click();
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建应用');

    // 填写表单 - 使用对话框内的表单元素
    const dialog = page.locator('.el-dialog');
    await dialog.locator('input[placeholder*="请输入应用名称"]').fill(createdApp.name);
    await dialog.locator('input[placeholder*="字母、数字、下划线"]').fill(createdApp.code);
    await dialog.locator('textarea[placeholder*="请输入应用描述"]').fill(createdApp.description);

    // 提交表单
    await page.locator('.el-dialog__footer button:has-text("确定")').click();

    // 验证创建成功
    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await page.waitForTimeout(1000);
    await expect(page.locator('.el-dialog')).not.toBeVisible();

    // 验证应用出现在表格中
    await expect(page.locator('.el-table__body')).toContainText(createdApp.name);
  });

  test('3. 搜索应用 - 按名称', async () => {
    await page.waitForTimeout(2000);

    if (createdApp) {
      // 按名称搜索
      await page.locator('.filter-form input[placeholder*="搜索应用"]').fill(createdApp.name);
      await page.locator('.filter-form button:has-text("搜索")').click();
      await page.waitForTimeout(1000);

      // 验证搜索结果
      await expect(page.locator('.el-table__body')).toContainText(createdApp.name);

      // 重置搜索
      await page.locator('.filter-form button:has-text("重置")').click();
      await page.waitForTimeout(1000);
    }
  });

  test('4. 搜索应用 - 按编码', async () => {
    await page.waitForTimeout(2000);

    if (createdApp) {
      // 按编码搜索
      await page.locator('.filter-form input[placeholder*="搜索应用"]').fill(createdApp.code);
      await page.locator('.filter-form button:has-text("搜索")').click();
      await page.waitForTimeout(1000);

      // 验证搜索结果
      await expect(page.locator('.el-table__body')).toContainText(createdApp.code);

      // 重置搜索
      await page.locator('.filter-form button:has-text("重置")').click();
      await page.waitForTimeout(1000);
    }
  });

  test('5. 编辑应用', async () => {
    // 如果没有创建过应用，先创建一个
    if (!createdApp) {
      createdApp = generateAppData();
      await page.locator('button:has-text("新建")').first().click();
      const dialog = page.locator('.el-dialog');
      await dialog.locator('input[placeholder*="请输入应用名称"]').fill(createdApp.name);
      await dialog.locator('input[placeholder*="字母、数字、下划线"]').fill(createdApp.code);
      await page.locator('.el-dialog__footer button:has-text("确定")').click();
      await page.waitForTimeout(2000);
    }

    // 在表格中找到应用
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    const rows = page.locator('.el-table__row');
    let targetRow = null;

    for (let i = 0; i < await rows.count(); i++) {
      const row = rows.nth(i);
      const text = await row.textContent();
      if (text && text.includes(createdApp.name)) {
        targetRow = row;
        break;
      }
    }

    expect(targetRow).not.toBeNull();

    // 点击编辑
    await targetRow.locator('button:has-text("编辑")').click();
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('编辑应用');

    // 生成新名称
    updatedAppName = generateAppName();

    // 更新表单 - 使用对话框内的表单元素
    const dialog = page.locator('.el-dialog');
    const nameInput = dialog.locator('input[placeholder*="请输入应用名称"]');
    await nameInput.clear();
    await nameInput.fill(updatedAppName);

    // 提交
    await page.locator('.el-dialog__footer button:has-text("确定")').click();

    // 验证更新成功
    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await page.waitForTimeout(1000);

    // 验证更新后的名称出现在表格中
    await expect(page.locator('.el-table__body')).toContainText(updatedAppName);
  });

  test('6. 删除应用', async () => {
    // 确定要删除的应用名称
    const appNameToDelete = updatedAppName || (createdApp ? createdApp.name : null);

    // 如果没有可删除的应用，创建一个
    if (!appNameToDelete) {
      createdApp = generateAppData();
      await page.locator('button:has-text("新建")').first().click();
      const dialog = page.locator('.el-dialog');
      await dialog.locator('input[placeholder*="请输入应用名称"]').fill(createdApp.name);
      await dialog.locator('input[placeholder*="字母、数字、下划线"]').fill(createdApp.code);
      await page.locator('.el-dialog__footer button:has-text("确定")').click();
      await page.waitForTimeout(2000);
    }

    const nameToDelete = appNameToDelete || createdApp.name;

    // 在表格中找到应用
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    const rows = page.locator('.el-table__row');
    let targetRow = null;

    for (let i = 0; i < await rows.count(); i++) {
      const row = rows.nth(i);
      const text = await row.textContent();
      if (text && text.includes(nameToDelete)) {
        targetRow = row;
        break;
      }
    }

    // 如果找不到，使用第一个应用
    if (!targetRow) {
      targetRow = rows.first();
    }

    expect(targetRow).not.toBeNull();

    // 点击删除
    await targetRow.locator('button:has-text("删除")').click();

    // 确认删除
    await expect(page.locator('.el-message-box')).toBeVisible();
    await expect(page.locator('.el-message-box__message')).toContainText('确定要删除');
    await page.locator('.el-message-box__btns button:has-text("确定")').click();

    // 验证删除成功
    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await page.waitForTimeout(1000);

    // 验证应用已被删除
    const tableContent = await page.locator('.el-table__body').textContent();
    expect(tableContent).not.toContain(nameToDelete);
  });
});
