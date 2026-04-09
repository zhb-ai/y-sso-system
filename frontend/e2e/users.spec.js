/**
 * 用户管理页面 E2E 测试
 * 优化：使用 test.describe.serial 只登录一次，所有测试共享登录状态
 */
import { test, expect } from './fixtures/test-base.js';
import { navigateToPage } from './fixtures/test-base.js';
import { generateUserData, generateDisplayName, generateEmail, generatePhone } from './fixtures/test-data.js';

test.describe.serial('用户管理页面 - 完整测试流程', () => {
  // 存储测试过程中创建的用户信息
  let createdUser = null;
  let updatedUserName = null;
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
    // 导航到用户管理页面
    await navigateToPage(page, '用户管理');

    // 验证页面标题
    await expect(page.locator('h2').first()).toContainText('用户管理');

    // 验证搜索区域
    await expect(page.locator('.filter-form')).toBeVisible();

    // 验证表格
    await expect(page.locator('.el-table')).toBeVisible();
    await page.waitForSelector('.el-table__row', { timeout: 10000 });

    // 验证操作按钮
    await expect(page.locator('button:has-text("编辑")').first()).toBeVisible();
    await expect(page.locator('button:has-text("角色")').first()).toBeVisible();
    await expect(page.locator('button:has-text("SSO")').first()).toBeVisible();
    await expect(page.locator('button:has-text("新建")').first()).toBeVisible();
  });

  test('2. 新建用户', async () => {
    // 生成随机用户数据
    createdUser = generateUserData();

    // 点击新建按钮
    await page.locator('button:has-text("新建")').first().click();
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建用户');

    // 填写表单 - 使用对话框内的表单元素
    const dialog = page.locator('.el-dialog');
    await dialog.locator('input[placeholder*="请输入用户名"]').fill(createdUser.username);
    await dialog.locator('input[placeholder*="姓名"]').fill(createdUser.displayName);
    await dialog.locator('input[placeholder*="邮箱"]').fill(createdUser.email);
    await dialog.locator('input[placeholder*="手机"]').fill(createdUser.phone);
    await dialog.locator('input[placeholder*="密码"]').fill(createdUser.password);

    // 提交表单
    await page.locator('.el-dialog__footer button:has-text("确定")').click();

    // 验证创建成功
    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await page.waitForTimeout(1000);
    await expect(page.locator('.el-dialog')).not.toBeVisible();

    // 验证用户出现在表格中
    await expect(page.locator('.el-table__body')).toContainText(createdUser.username);
  });

  test('3. 搜索用户 - 按用户名', async () => {
    await page.waitForTimeout(2000);

    if (createdUser) {
      // 按用户名搜索
      const searchInput = page.locator('.filter-form input[type="text"]').first();
      await searchInput.fill(createdUser.username);
      await page.locator('.filter-form button:has-text("搜索")').click();
      await page.waitForTimeout(1000);

      // 验证搜索结果
      await expect(page.locator('.el-table__body')).toContainText(createdUser.username);

      // 重置搜索
      await page.locator('.filter-form button:has-text("重置")').click();
      await page.waitForTimeout(1000);
    }
  });

  test('4. 搜索用户 - 按邮箱', async () => {
    await page.waitForTimeout(2000);

    if (createdUser) {
      // 按邮箱搜索
      const searchInput = page.locator('.filter-form input[type="text"]').first();
      await searchInput.fill(createdUser.email);
      await page.locator('.filter-form button:has-text("搜索")').click();
      await page.waitForTimeout(1000);

      // 验证搜索结果
      await expect(page.locator('.el-table__body')).toContainText(createdUser.email);

      // 重置搜索
      await page.locator('.filter-form button:has-text("重置")').click();
      await page.waitForTimeout(1000);
    }
  });

  test('5. 编辑用户', async () => {
    // 如果没有创建过用户，先创建一个
    if (!createdUser) {
      createdUser = generateUserData();
      await page.locator('button:has-text("新建")').first().click();
      const dialog = page.locator('.el-dialog');
      await dialog.locator('input[placeholder*="请输入用户名"]').fill(createdUser.username);
      await dialog.locator('input[placeholder*="姓名"]').fill(createdUser.displayName);
      await dialog.locator('input[placeholder*="邮箱"]').fill(createdUser.email);
      await page.locator('.el-dialog__footer button:has-text("确定")').click();
      await page.waitForTimeout(2000);
    }

    const nameToDelete = userNameToDelete || createdUser.username;

    // 在表格中找到用户
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    const rows = page.locator('.el-table__row');
    let targetRow = null;

    for (let i = 0; i < await rows.count(); i++) {
      const row = rows.nth(i);
      const text = await row.textContent();
      if (text && text.includes(createdUser.username)) {
        targetRow = row;
        break;
      }
    }

    expect(targetRow).not.toBeNull();

    // 点击编辑
    await targetRow.locator('button:has-text("编辑")').click();
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('编辑用户');

    // 生成新姓名和邮箱
    updatedUserName = generateDisplayName();
    const newEmail = generateEmail();

    // 更新表单 - 使用对话框内的表单元素
    const editDialog = page.locator('.el-dialog');
    const nameInput = editDialog.locator('input[placeholder*="姓名"]');
    await nameInput.clear();
    await nameInput.fill(updatedUserName);

    const emailInput = editDialog.locator('input[placeholder*="邮箱"]');
    await emailInput.clear();
    await emailInput.fill(newEmail);

    // 提交
    await page.locator('.el-dialog__footer button:has-text("确定")').click();

    // 验证更新成功
    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await page.waitForTimeout(1000);

    // 验证更新后的姓名出现在表格中
    await expect(page.locator('.el-table__body')).toContainText(updatedUserName);
  });

  test('6. 角色分配功能', async () => {
    await page.waitForTimeout(2000);

    // 在表格中找到用户
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    const rows = page.locator('.el-table__row');
    let targetRow = null;

    for (let i = 0; i < await rows.count(); i++) {
      const row = rows.nth(i);
      const text = await row.textContent();
      if (text && text.includes(createdUser ? createdUser.username : '')) {
        targetRow = row;
        break;
      }
    }

    // 如果找不到，使用第一行
    if (!targetRow) {
      targetRow = rows.first();
    }

    expect(targetRow).not.toBeNull();

    // 点击角色分配
    await targetRow.locator('button:has-text("角色")').click();
    await expect(page.locator('.el-drawer')).toBeVisible();
    await expect(page.locator('.el-drawer__header')).toContainText('角色');

    // 等待角色列表加载
    await page.waitForTimeout(1000);

    // 关闭抽屉
    await page.locator('.el-drawer__close-btn, button:has-text("关闭")').first().click();
    await page.waitForTimeout(500);
  });

  test('7. 禁用/启用用户', async () => {
    // 在表格中找到用户
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    const rows = page.locator('.el-table__row');
    let targetRow = null;

    for (let i = 0; i < await rows.count(); i++) {
      const row = rows.nth(i);
      const text = await row.textContent();
      if (text && text.includes(createdUser ? createdUser.username : '')) {
        targetRow = row;
        break;
      }
    }

    // 如果找不到，使用第一行
    if (!targetRow) {
      targetRow = rows.first();
    }

    expect(targetRow).not.toBeNull();

    // 获取当前状态
    const rowText = await targetRow.textContent();
    const isActive = rowText.includes('启用');

    // 点击禁用/启用按钮
    const toggleButton = targetRow.locator('button:has-text("禁用"), button:has-text("启用")').first();
    await toggleButton.click();

    // 等待操作完成
    await page.waitForTimeout(1000);

    // 验证操作成功（通过检查提示消息或状态变化）
    await expect(page.locator('.el-message--success')).toBeVisible({ timeout: 10000 });
  });
});
