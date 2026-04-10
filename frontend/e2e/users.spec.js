/**
 * 用户管理页面 E2E 测试
 * 使用全局共享登录状态，避免并发登录冲突
 */
import { test, expect } from '@playwright/test';
import { navigateTo, ROUTES } from './fixtures/shared-auth.js';
import { generateUserData, generateDisplayName, generateEmail, generatePhone } from './fixtures/test-data.js';

test.describe.serial('用户管理页面 - 完整测试流程', () => {
  let createdUser = null;
  let updatedUserName = null;
  let page;

  test.beforeAll(async ({ browser }) => {
    const context = await browser.newContext({
      storageState: 'playwright/.auth/user.json'
    });
    page = await context.newPage();

    console.log('[用户管理] 开始测试...');
    await navigateTo(page, ROUTES.USERS);
    console.log('[用户管理] 页面准备完成');
  });

  test.afterAll(async () => {
    if (page) {
      await page.context().close();
    }
  });

  test('1. 页面元素验证', async () => {
    await expect(page.locator('h2').first()).toContainText('用户管理');
    await expect(page.locator('.filter-form')).toBeVisible();
    await expect(page.locator('.el-table')).toBeVisible();
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    await expect(page.locator('button:has-text("编辑")').first()).toBeVisible();
    await expect(page.locator('button:has-text("角色")').first()).toBeVisible();
    await expect(page.locator('button:has-text("SSO")').first()).toBeVisible();
    await expect(page.locator('button:has-text("新建")').first()).toBeVisible();
  });

  test('2. 新建用户', async () => {
    createdUser = generateUserData();

    await page.locator('button:has-text("新建")').first().click();
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建用户');

    const dialog = page.locator('.el-dialog');
    await dialog.locator('input[placeholder*="请输入用户名"]').fill(createdUser.username);
    await dialog.locator('input[placeholder*="姓名"]').fill(createdUser.displayName);
    await dialog.locator('input[placeholder*="邮箱"]').fill(createdUser.email);
    await dialog.locator('input[placeholder*="手机"]').fill(createdUser.phone);
    await dialog.locator('input[placeholder*="密码"]').fill(createdUser.password);

    await page.locator('.el-dialog__footer button:has-text("确定")').click();

    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await page.waitForTimeout(1000);
    await expect(page.locator('.el-dialog')).not.toBeVisible();

    await expect(page.locator('.el-table__body')).toContainText(createdUser.username);
  });

  test('3. 搜索用户 - 按用户名', async () => {
    await page.waitForTimeout(2000);

    if (createdUser) {
      const searchInput = page.locator('.filter-form input[type="text"]').first();
      await searchInput.fill(createdUser.username);
      await page.locator('.filter-form button:has-text("搜索")').click();
      await page.waitForTimeout(1000);

      await expect(page.locator('.el-table__body')).toContainText(createdUser.username);

      await page.locator('.filter-form button:has-text("重置")').click();
      await page.waitForTimeout(1000);
    }
  });

  test('4. 搜索用户 - 按邮箱', async () => {
    await page.waitForTimeout(2000);

    if (createdUser) {
      const searchInput = page.locator('.filter-form input[type="text"]').first();
      await searchInput.fill(createdUser.email);
      await page.locator('.filter-form button:has-text("搜索")').click();
      await page.waitForTimeout(1000);

      await expect(page.locator('.el-table__body')).toContainText(createdUser.email);

      await page.locator('.filter-form button:has-text("重置")').click();
      await page.waitForTimeout(1000);
    }
  });

  test('5. 编辑用户', async () => {
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

    await targetRow.locator('button:has-text("编辑")').click();
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('编辑用户');

    updatedUserName = generateDisplayName();
    const newEmail = generateEmail();

    const editDialog = page.locator('.el-dialog');
    const nameInput = editDialog.locator('input[placeholder*="姓名"]');
    await nameInput.clear();
    await nameInput.fill(updatedUserName);

    const emailInput = editDialog.locator('input[placeholder*="邮箱"]');
    await emailInput.clear();
    await emailInput.fill(newEmail);

    await page.locator('.el-dialog__footer button:has-text("确定")').click();

    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await page.waitForTimeout(1000);

    await expect(page.locator('.el-table__body')).toContainText(updatedUserName);
  });

  test('6. 角色分配功能', async () => {
    await page.waitForTimeout(2000);

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

    if (!targetRow) {
      targetRow = rows.first();
    }

    expect(targetRow).not.toBeNull();

    await targetRow.locator('button:has-text("角色")').click();
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('分配角色');

    await page.waitForTimeout(1000);

    await page.locator('.el-dialog__footer button:has-text("取消")').click();
    await page.waitForTimeout(500);
  });

  test('7. 禁用/启用用户', async () => {
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

    if (!targetRow) {
      targetRow = rows.first();
    }

    expect(targetRow).not.toBeNull();

    const rowText = await targetRow.textContent();
    const isActive = rowText.includes('启用');

    const toggleButton = targetRow.locator('button:has-text("禁用"), button:has-text("启用")').first();
    await toggleButton.click();

    await expect(page.locator('.el-message-box')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.el-message-box__message')).toContainText(isActive ? '禁用' : '启用');

    await page.locator('.el-message-box__btns button:has-text("确定")').click();

    await page.waitForTimeout(1000);

    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
  });
});
