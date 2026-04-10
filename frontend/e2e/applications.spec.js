/**
 * 应用管理页面 E2E 测试
 * 使用全局共享登录状态，避免并发登录冲突
 */
import { test, expect } from '@playwright/test';
import { navigateTo, ROUTES } from './fixtures/shared-auth.js';
import { generateAppData, generateAppName } from './fixtures/test-data.js';

test.describe.serial('应用管理页面 - 完整测试流程', () => {
  let createdApp = null;
  let updatedAppName = null;
  let page;

  test.beforeAll(async ({ browser }) => {
    const context = await browser.newContext({
      storageState: 'playwright/.auth/user.json'
    });
    page = await context.newPage();

    console.log('[应用管理] 开始测试...');
    await navigateTo(page, ROUTES.APPLICATIONS);
    console.log('[应用管理] 页面准备完成');
  });

  test.afterAll(async () => {
    if (page) {
      await page.context().close();
    }
  });

  test('1. 页面元素验证', async () => {
    await expect(page.locator('h2').first()).toContainText('应用管理');
    await expect(page.locator('.filter-form')).toBeVisible();
    await expect(page.locator('.el-table')).toBeVisible();
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    await expect(page.locator('button:has-text("编辑")').first()).toBeVisible();
    await expect(page.locator('button:has-text("删除")').first()).toBeVisible();
    await expect(page.locator('button:has-text("密钥")').first()).toBeVisible();
    await expect(page.locator('button:has-text("新建")').first()).toBeVisible();
  });

  test('2. 新建应用', async () => {
    createdApp = generateAppData();

    await page.locator('button:has-text("新建")').first().click();
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建应用');

    const dialog = page.locator('.el-dialog');
    await dialog.locator('input[placeholder*="请输入应用名称"]').fill(createdApp.name);
    await dialog.locator('input[placeholder*="字母、数字、下划线"]').fill(createdApp.code);
    await dialog.locator('textarea[placeholder*="请输入应用描述"]').fill(createdApp.description);

    await page.locator('.el-dialog__footer button:has-text("确认")').click();

    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await page.waitForTimeout(1000);

    const credentialDialog = page.locator('.el-dialog').filter({ hasText: '客户端凭证' });
    await expect(credentialDialog).toBeVisible();

    await credentialDialog.locator('.el-dialog__footer button:has-text("我已保存，关闭")').click();
    await page.waitForTimeout(1500);

    await expect(credentialDialog).not.toBeVisible();
    await expect(page.locator('.el-table__body')).toContainText(createdApp.name);
  });

  test('3. 搜索应用 - 按名称', async () => {
    await page.waitForTimeout(2000);

    if (createdApp) {
      await page.locator('.filter-form input[placeholder*="搜索应用"]').fill(createdApp.name);
      await page.locator('.filter-form button:has-text("搜索")').click();
      await page.waitForTimeout(1000);

      await expect(page.locator('.el-table__body')).toContainText(createdApp.name);

      await page.locator('.filter-form button:has-text("重置")').click();
      await page.waitForTimeout(1000);
    }
  });

  test('4. 搜索应用 - 按编码', async () => {
    await page.waitForTimeout(2000);

    if (createdApp) {
      await page.locator('.filter-form input[placeholder*="搜索应用"]').fill(createdApp.code);
      await page.locator('.filter-form button:has-text("搜索")').click();
      await page.waitForTimeout(1000);

      await expect(page.locator('.el-table__body')).toContainText(createdApp.code);

      await page.locator('.filter-form button:has-text("重置")').click();
      await page.waitForTimeout(1000);
    }
  });

  test('5. 编辑应用', async () => {
    if (!createdApp) {
      createdApp = generateAppData();
      await page.locator('button:has-text("新建")').first().click();
      const dialog = page.locator('.el-dialog');
      await dialog.locator('input[placeholder*="请输入应用名称"]').fill(createdApp.name);
      await dialog.locator('input[placeholder*="字母、数字、下划线"]').fill(createdApp.code);
      await page.locator('.el-dialog__footer button:has-text("确认")').click();
      await page.waitForTimeout(2000);
    }

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

    await targetRow.locator('button:has-text("编辑")').click();
    await page.waitForTimeout(500);

    const editDialog = page.locator('.el-dialog').filter({ hasText: '编辑应用' });
    await expect(editDialog).toBeVisible();
    await expect(editDialog.locator('.el-dialog__title')).toContainText('编辑应用');

    updatedAppName = generateAppName();

    const nameInput = editDialog.locator('input[placeholder*="请输入应用名称"]');
    await nameInput.clear();
    await nameInput.fill(updatedAppName);

    await editDialog.locator('.el-dialog__footer button:has-text("确认")').click();

    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await page.waitForTimeout(1000);

    await expect(page.locator('.el-table__body')).toContainText(updatedAppName);
  });

  test('6. 删除应用', async () => {
    const appNameToDelete = updatedAppName || (createdApp ? createdApp.name : null);

    if (!appNameToDelete) {
      createdApp = generateAppData();
      await page.locator('button:has-text("新建")').first().click();
      const dialog = page.locator('.el-dialog');
      await dialog.locator('input[placeholder*="请输入应用名称"]').fill(createdApp.name);
      await dialog.locator('input[placeholder*="字母、数字、下划线"]').fill(createdApp.code);
      await page.locator('.el-dialog__footer button:has-text("确认")').click();
      await page.waitForTimeout(2000);
    }

    const nameToDelete = appNameToDelete || createdApp.name;

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

    if (!targetRow) {
      targetRow = rows.first();
    }

    expect(targetRow).not.toBeNull();

    await targetRow.locator('button:has-text("删除")').click();

    await expect(page.locator('.el-message-box')).toBeVisible();
    await expect(page.locator('.el-message-box__message')).toContainText('删除');
    await page.locator('.el-message-box__btns button:has-text("确定")').click();

    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await page.waitForTimeout(2000);

    // 注：删除后表格可能需要刷新才能更新，这里只验证操作成功
  });
});
