/**
 * 角色管理页面 E2E 测试
 * 使用全局共享登录状态，避免并发登录冲突
 */
import { test, expect } from '@playwright/test';
import { navigateTo, ROUTES } from './fixtures/shared-auth.js';
import { generateRoleData, generateRoleName, generateRoleDescription } from './fixtures/test-data.js';

function getPermissionDrawer(page) {
  return page.locator('.el-drawer').filter({ has: page.locator('.el-drawer__header', { hasText: '分配权限' }) });
}

test.describe.serial('角色管理页面 - 完整测试流程', () => {
  let createdRole = null;
  let updatedRoleName = null;
  let page;

  test.beforeAll(async ({ browser }) => {
    const context = await browser.newContext({
      storageState: 'playwright/.auth/user.json'
    });
    page = await context.newPage();

    console.log('[角色管理] 开始测试...');
    await navigateTo(page, ROUTES.ROLES);
    console.log('[角色管理] 页面准备完成');
  });

  test.afterAll(async () => {
    if (page) {
      await page.context().close();
    }
  });

  test('1. 页面元素验证', async () => {
    await expect(page.locator('h2').first()).toContainText('角色管理');
    await expect(page.locator('.el-table')).toBeVisible();
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    await expect(page.locator('button:has-text("编辑")').first()).toBeVisible();
    await expect(page.locator('button:has-text("删除")').first()).toBeVisible();
    await expect(page.locator('button:has-text("权限")').first()).toBeVisible();
    await expect(page.locator('button:has-text("新建")').first()).toBeVisible();
  });

  test('2. 新建角色', async () => {
    createdRole = generateRoleData();

    await page.locator('button:has-text("新建")').first().click();
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建角色');

    await page.locator('input[placeholder*="admin"]').fill(createdRole.code);
    await page.locator('input[placeholder*="管理员"]').fill(createdRole.name);
    await page.locator('textarea[placeholder*="描述"]').fill(createdRole.description);

    await page.locator('.el-dialog__footer button:has-text("确定")').click();

    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await expect(page.locator('.el-dialog')).not.toBeVisible();

    await expect(page.locator('.el-table__body')).toContainText(createdRole.name);
  });

  test('3. 编辑角色', async () => {
    if (!createdRole) {
      createdRole = generateRoleData();
      await page.locator('button:has-text("新建")').first().click();
      await page.locator('input[placeholder*="admin"]').fill(createdRole.code);
      await page.locator('input[placeholder*="管理员"]').fill(createdRole.name);
      await page.locator('.el-dialog__footer button:has-text("确定")').click();
      await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
      await expect(page.locator('.el-message--success').first()).toContainText('成功');
      await expect(page.locator('.el-dialog')).not.toBeVisible();
      await expect(page.locator('.el-table__body')).toContainText(createdRole.name);
    }

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

    await targetRow.locator('button:has-text("编辑")').click();
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('编辑角色');

    updatedRoleName = generateRoleName();
    const newDescription = generateRoleDescription();

    const nameInput = page.locator('input[placeholder*="管理员"]');
    await nameInput.clear();
    await nameInput.fill(updatedRoleName);

    const descInput = page.locator('textarea[placeholder*="描述"]');
    await descInput.clear();
    await descInput.fill(newDescription);

    await page.locator('.el-dialog__footer button:has-text("确定")').click();

    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');

    await expect(page.locator('.el-table__body')).toContainText(updatedRoleName);
  });

  test('4. 权限分配功能', async () => {
    await page.waitForSelector('.el-table__row', { timeout: 10000 });

    const roleName = updatedRoleName || createdRole?.name;
    expect(roleName).toBeTruthy();

    // 重新定位角色行，避免按钮点击后 DOM 变化导致引用失效
    const rows = page.locator('.el-table__row');
    let targetRow = null;
    for (let i = 0; i < await rows.count(); i++) {
      const row = rows.nth(i);
      const text = await row.textContent();
      if (text && text.includes(roleName)) {
        targetRow = row;
        break;
      }
    }

    expect(targetRow).not.toBeNull();

    await targetRow.locator('button:has-text("权限")').click();
    const permissionDrawer = getPermissionDrawer(page);
    await expect(permissionDrawer).toBeVisible();
    await expect(permissionDrawer.locator('.el-drawer__header')).toContainText('分配权限');

    // 这条用例期望是非 admin 角色（admin 会禁用复选框）
    await expect(permissionDrawer.locator('.el-alert__title:has-text("admin 角色自动拥有所有权限")')).toHaveCount(0);

    const checkbox = permissionDrawer.locator('.perm-checkbox').first();
    await checkbox.waitFor({ state: 'visible', timeout: 10000 });

    const permCode = await checkbox.locator('.perm-code').first().innerText();
    const permInput = checkbox.locator('input[type="checkbox"]').first();
    await permInput.waitFor({ state: 'attached', timeout: 10000 });
    await expect(permInput).not.toBeDisabled();
    const wasChecked = await permInput.isChecked();

    // 切换该权限勾选状态
    await checkbox.click();

    await permissionDrawer.locator('.perm-drawer-footer button:has-text("保存")').first().click();

    await expect(page.locator('.el-message--success').first()).toContainText('权限保存成功');
    await expect(permissionDrawer).not.toBeVisible();

    // 再次打开抽屉，验证保存结果是否持久化
    // 注意：抽屉 close + destroy-on-close 后，需要重新打开并等待复选框重新加载
    await targetRow.locator('button:has-text("权限")').click();
    await expect(permissionDrawer).toBeVisible();

    const reopenedCheckbox = permissionDrawer.locator('.perm-checkbox').filter({ hasText: permCode }).first();
    await reopenedCheckbox.waitFor({ state: 'visible', timeout: 10000 });

    const reopenedInput = reopenedCheckbox.locator('input[type="checkbox"]').first();
    await reopenedInput.waitFor({ state: 'attached', timeout: 10000 });
    await expect(reopenedInput).not.toBeDisabled();

    const isCheckedNow = await reopenedInput.isChecked();
    expect(isCheckedNow).toBe(!wasChecked);

  });

  test('5. 删除角色', async () => {
    // 防止上一个用例的权限抽屉残留 overlay 拦截点击
    const permissionDrawer = getPermissionDrawer(page);
    if (await permissionDrawer.isVisible().catch(() => false)) {
      await permissionDrawer
        .locator('.el-drawer__close-btn, button:has-text("取消")')
        .first()
        .click();
      await expect(permissionDrawer).not.toBeVisible({ timeout: 10000 });
    }

    // WebKit 下 overlay 可能短暂存在（数量可能 > 1），这里只要确保点击目标前 overlay 不处于可见状态即可
    await page.locator('.el-overlay.is-drawer').first().waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});

    const roleNameToDelete = updatedRoleName || (createdRole ? createdRole.name : null);

    if (!roleNameToDelete) {
      createdRole = generateRoleData();
      await page.locator('button:has-text("新建")').first().click();
      await page.locator('input[placeholder*="admin"]').fill(createdRole.code);
      await page.locator('input[placeholder*="管理员"]').fill(createdRole.name);
      await page.locator('.el-dialog__footer button:has-text("确定")').click();
      await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
      await expect(page.locator('.el-message--success').first()).toContainText('成功');
      await expect(page.locator('.el-table__body')).toContainText(createdRole.name);
    }

    const nameToDelete = roleNameToDelete || createdRole.name;

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

    await targetRow.locator('button:has-text("删除")').first().click();

    await expect(page.locator('.el-message-box')).toBeVisible();
    await expect(page.locator('.el-message-box__message')).toContainText('确定要删除');
    await page.locator('.el-message-box__btns button:has-text("确定")').click();

    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');

    // 等待被删除的角色从表格中消失（避免 Firefox 下 toast 先出现导致的文本残留）
    const roleRows = page.locator('.el-table__row').filter({ hasText: nameToDelete });
    await expect(roleRows).toHaveCount(0, { timeout: 15000 });
  });
});
