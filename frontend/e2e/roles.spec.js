/**
 * 角色管理页面 E2E 测试
 * 优化：使用 test.describe.serial 只登录一次，所有测试共享登录状态
 */
import { test, expect } from './fixtures/test-base.js';
import { navigateToPage } from './fixtures/test-base.js';
import { generateRoleData, generateRoleName, generateRoleDescription } from './fixtures/test-data.js';

test.describe.serial('角色管理页面 - 完整测试流程', () => {
  // 存储测试过程中创建的角色信息
  let createdRole = null;
  let updatedRoleName = null;
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
    // 导航到角色管理页面
    await navigateToPage(page, '角色管理');

    // 验证页面标题
    await expect(page.locator('h2').first()).toContainText('角色管理');

    // 验证表格
    await expect(page.locator('.el-table')).toBeVisible();
    await page.waitForSelector('.el-table__row', { timeout: 10000 });

    // 验证操作按钮
    await expect(page.locator('button:has-text("编辑")').first()).toBeVisible();
    await expect(page.locator('button:has-text("删除")').first()).toBeVisible();
    await expect(page.locator('button:has-text("权限")').first()).toBeVisible();
    await expect(page.locator('button:has-text("新建")').first()).toBeVisible();
  });

  test('2. 新建角色', async () => {
    // 生成随机角色数据
    createdRole = generateRoleData();

    // 点击新建按钮
    await page.locator('button:has-text("新建")').first().click();
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建角色');

    // 填写表单
    await page.locator('input[placeholder*="admin"]').fill(createdRole.code);
    await page.locator('input[placeholder*="管理员"]').fill(createdRole.name);
    await page.locator('textarea[placeholder*="描述"]').fill(createdRole.description);

    // 提交表单
    await page.locator('.el-dialog__footer button:has-text("确定")').click();

    // 验证创建成功
    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await page.waitForTimeout(1000);
    await expect(page.locator('.el-dialog')).not.toBeVisible();

    // 验证角色出现在表格中
    await expect(page.locator('.el-table__body')).toContainText(createdRole.name);
  });

  test('3. 编辑角色', async () => {
    // 如果没有创建过角色，先创建一个
    if (!createdRole) {
      createdRole = generateRoleData();
      await page.locator('button:has-text("新建")').first().click();
      await page.locator('input[placeholder*="admin"]').fill(createdRole.code);
      await page.locator('input[placeholder*="管理员"]').fill(createdRole.name);
      await page.locator('.el-dialog__footer button:has-text("确定")').click();
      await page.waitForTimeout(2000);
    }

    // 在表格中找到角色
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    const rows = page.locator('.el-table__row');
    let targetRow = null;

    for (let i = 0; i < await rows.count(); i++) {
      const row = rows.nth(i);
      const text = await row.textContent();
      if (text && text.includes(createdRole.name)) {
        targetRow = row;
        break;
      }
    }

    expect(targetRow).not.toBeNull();

    // 点击编辑
    await targetRow.locator('button:has-text("编辑")').click();
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('编辑角色');

    // 生成新名称和描述
    updatedRoleName = generateRoleName();
    const newDescription = generateRoleDescription();

    // 更新表单
    const nameInput = page.locator('input[placeholder*="管理员"]');
    await nameInput.clear();
    await nameInput.fill(updatedRoleName);

    const descInput = page.locator('textarea[placeholder*="描述"]');
    await descInput.clear();
    await descInput.fill(newDescription);

    // 提交
    await page.locator('.el-dialog__footer button:has-text("确定")').click();

    // 验证更新成功
    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await page.waitForTimeout(1000);

    // 验证更新后的名称出现在表格中
    await expect(page.locator('.el-table__body')).toContainText(updatedRoleName);
  });

  test('4. 权限分配功能', async () => {
    await page.waitForTimeout(2000);

    // 在表格中找到角色
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    const rows = page.locator('.el-table__row');
    let targetRow = null;

    for (let i = 0; i < await rows.count(); i++) {
      const row = rows.nth(i);
      const text = await row.textContent();
      if (text && text.includes(updatedRoleName || createdRole.name)) {
        targetRow = row;
        break;
      }
    }

    // 如果找不到，使用第一行
    if (!targetRow) {
      targetRow = rows.first();
    }

    expect(targetRow).not.toBeNull();

    // 点击权限分配
    await targetRow.locator('button:has-text("权限")').click();
    await expect(page.locator('.el-drawer')).toBeVisible();
    await expect(page.locator('.el-drawer__header')).toContainText('权限');

    // 等待权限树加载
    await page.waitForTimeout(1000);

    // 关闭权限分配抽屉
    await page.locator('.el-drawer__close-btn, button:has-text("关闭")').first().click();
    await page.waitForTimeout(500);
  });

  test('5. 删除角色', async () => {
    // 确定要删除的角色名称
    const roleNameToDelete = updatedRoleName || (createdRole ? createdRole.name : null);

    // 如果没有可删除的角色，创建一个
    if (!roleNameToDelete) {
      createdRole = generateRoleData();
      await page.locator('button:has-text("新建")').first().click();
      await page.locator('input[placeholder*="admin"]').fill(createdRole.code);
      await page.locator('input[placeholder*="管理员"]').fill(createdRole.name);
      await page.locator('.el-dialog__footer button:has-text("确定")').click();
      await page.waitForTimeout(2000);
    }

    const nameToDelete = roleNameToDelete || createdRole.name;

    // 在表格中找到角色
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

    // 如果找不到，使用第一个可删除的角色
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

    // 验证角色已被删除
    const tableContent = await page.locator('.el-table__body').textContent();
    expect(tableContent).not.toContain(nameToDelete);
  });
});
