/**
 * SSO角色管理页面 E2E 测试
 * 优化：直接访问SSO角色页面，如果token不存在或失效则自动登录
 */
import { test, expect, smartNavigate } from './fixtures/smart-test-base.js';
import { generateRoleData, generateRoleName, generateRoleDescription } from './fixtures/test-data.js';
import { ROUTES } from './fixtures/test-config.js';

/**
 * 生成SSO角色专用随机数据
 * @returns {Object}
 */
function generateSSORoleData() {
  const baseData = generateRoleData();
  return {
    ...baseData,
    sortOrder: Math.floor(Math.random() * 100)
  };
}

test.describe.serial('SSO角色管理页面 - 完整测试流程', () => {
  // 存储测试过程中创建的角色信息
  let createdRole = null;
  let updatedRoleName = null;
  let page;
  let context;

  test.beforeAll(async ({ browser }) => {
    // 创建新的浏览器上下文
    context = await browser.newContext();
    page = await context.newPage();

    // 直接访问SSO角色页面，smartNavigate会自动处理登录
    console.log('[SSO角色] 开始测试，直接访问页面...');
    await smartNavigate(page, ROUTES.SSO_ROLES, { checkAuth: true });
    console.log('[SSO角色] 页面准备完成');
  });

  test.afterAll(async () => {
    // 所有测试结束后关闭上下文
    if (context) {
      await context.close();
    }
  });

  test('1. 页面元素验证', async () => {
    // 验证页面标题
    await expect(page.locator('.page-header h2')).toContainText('SSO');

    // 验证搜索区域元素
    await expect(page.locator('.filter-form')).toBeVisible();
    await expect(page.locator('input[placeholder="搜索角色名称或编码"]')).toBeVisible();
    await expect(page.locator('.el-select')).toBeVisible();
    await expect(page.locator('button:has-text("搜索")')).toBeVisible();
    await expect(page.locator('button:has-text("重置")')).toBeVisible();

    // 验证表格和操作按钮
    await expect(page.locator('.el-table')).toBeVisible();
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    await expect(page.locator('button:has-text("编辑")').first()).toBeVisible();
    await expect(page.locator('button:has-text("删除")').first()).toBeVisible();
    await expect(page.getByRole('button', { name: '新建' }).first()).toBeVisible();
  });

  test('2. 新建SSO角色', async () => {
    // 生成随机SSO角色数据
    createdRole = generateSSORoleData();

    // 点击新建按钮
    await page.getByRole('button', { name: '新建 SSO 角色' }).click();
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建 SSO 角色');

    // 填写表单
    await page.locator('input[placeholder="如 finance_admin, hr_viewer"]').fill(createdRole.code);
    await page.locator('input[placeholder="如 财务管理员"]').fill(createdRole.name);
    await page.locator('textarea[placeholder="角色描述（选填）"]').fill(createdRole.description);

    // 设置排序值
    const sortInput = page.locator('.el-input-number input');
    await sortInput.clear();
    await sortInput.fill(createdRole.sortOrder.toString());

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

  test('3. 搜索功能 - 按名称搜索', async () => {
    await page.waitForTimeout(2000);

    // 使用创建的角色名称搜索
    if (createdRole) {
      const searchInput = page.locator('input[placeholder="搜索角色名称或编码"]');
      await searchInput.fill(createdRole.name);
      await page.locator('button:has-text("搜索")').click();
      await page.waitForTimeout(1000);

      // 验证搜索结果
      await expect(page.locator('.el-table__body')).toContainText(createdRole.name);

      // 重置搜索
      await page.locator('button:has-text("重置")').click();
      await page.waitForTimeout(1000);
    }
  });

  test('4. 搜索功能 - 按编码搜索', async () => {
    await page.waitForTimeout(2000);

    // 使用创建的角色编码搜索
    if (createdRole) {
      const searchInput = page.locator('input[placeholder="搜索角色名称或编码"]');
      await searchInput.fill(createdRole.code);
      await page.locator('button:has-text("搜索")').click();
      await page.waitForTimeout(1000);

      // 验证搜索结果
      await expect(page.locator('.el-table__body')).toContainText(createdRole.code);

      // 重置搜索
      await page.locator('button:has-text("重置")').click();
      await page.waitForTimeout(1000);
    }
  });

  test('5. 编辑SSO角色', async () => {
    // 如果没有创建过角色，先创建一个
    if (!createdRole) {
      createdRole = generateSSORoleData();
      await page.getByRole('button', { name: '新建 SSO 角色' }).click();
      await page.locator('input[placeholder="如 finance_admin, hr_viewer"]').fill(createdRole.code);
      await page.locator('input[placeholder="如 财务管理员"]').fill(createdRole.name);
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
    await expect(page.locator('.el-dialog__title')).toContainText('编辑 SSO 角色');

    // 生成新名称和描述
    updatedRoleName = generateRoleName();
    const newDescription = generateRoleDescription();

    // 更新表单
    const nameInput = page.locator('input[placeholder="如 财务管理员"]');
    await nameInput.clear();
    await nameInput.fill(updatedRoleName);

    const descInput = page.locator('textarea[placeholder="角色描述（选填）"]');
    await descInput.clear();
    await descInput.fill(newDescription);

    // 切换状态
    const switchElement = page.locator('.el-switch');
    if (await switchElement.count() > 0) {
      await switchElement.click();
      await page.waitForTimeout(300);
    }

    // 提交
    await page.locator('.el-dialog__footer button:has-text("确定")').click();

    // 验证更新成功
    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await page.waitForTimeout(1000);

    // 验证更新后的名称出现在表格中
    await expect(page.locator('.el-table__body')).toContainText(updatedRoleName);
  });

  test('6. 状态筛选功能', async () => {
    await page.waitForSelector('.el-table__row', { timeout: 10000 });

    // 点击状态下拉框
    const statusSelect = page.locator('.el-select').first();
    await statusSelect.click();
    await page.waitForTimeout(500);

    // 选择"启用"状态
    const activeOption = page.locator('.el-select-dropdown__item:has-text("启用")');
    if (await activeOption.count() > 0) {
      await activeOption.click();
      await page.waitForTimeout(1000);
      await page.locator('button:has-text("搜索")').click();
      await page.waitForTimeout(1000);
    }

    // 重置筛选
    await page.locator('button:has-text("重置")').click();
    await page.waitForTimeout(1000);
  });

  test('7. 删除SSO角色', async () => {
    // 确定要删除的角色名称
    const roleNameToDelete = updatedRoleName || (createdRole ? createdRole.name : null);

    // 如果没有可删除的角色，创建一个
    if (!roleNameToDelete) {
      createdRole = generateSSORoleData();
      await page.getByRole('button', { name: '新建 SSO 角色' }).click();
      await page.locator('input[placeholder="如 finance_admin, hr_viewer"]').fill(createdRole.code);
      await page.locator('input[placeholder="如 财务管理员"]').fill(createdRole.name);
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
