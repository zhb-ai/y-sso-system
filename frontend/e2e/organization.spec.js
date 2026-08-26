/**
 * 组织架构页面 E2E 测试
 * 使用全局共享登录状态，避免并发登录冲突
 */
import { test, expect } from '@playwright/test';
import { navigateTo, ROUTES } from './fixtures/shared-auth.js';
import { generateDepartmentName, generateDepartmentCode } from './fixtures/test-data.js';

test.describe.serial('组织架构页面 - 完整测试流程', () => {
  let createdDepartment = null;
  let updatedDepartmentName = null;
  let page;

  test.beforeAll(async ({ browser }) => {
    const context = await browser.newContext({
      storageState: 'playwright/.auth/user.json'
    });
    page = await context.newPage();

    console.log('[组织架构] 开始测试...');
    await navigateTo(page, ROUTES.ORGANIZATION);
    console.log('[组织架构] 页面准备完成');
  });

  test.afterAll(async () => {
    if (page) {
      await page.context().close();
    }
  });

  test('1. 页面元素验证', async () => {
    await expect(page.locator('h2').first()).toContainText('组织架构');
    await expect(page.locator('.el-tree')).toBeVisible();
    await expect(page.locator('.el-tree-node').first()).toBeVisible();
    await expect(page.locator('button:has-text("新建")').first()).toBeVisible();
    const employeeTable = page.locator('.employee-list-card .el-table');
    if (await employeeTable.isVisible()) {
      await expect(employeeTable.locator('.el-table__header').getByText('用户Id')).toBeVisible();
    }
  });

  test('2. 可以收起/展开部门树节点', async () => {
    // 等待部门树加载
    await page.waitForSelector('.el-tree-node', { timeout: 10000 });

    // 查找可展开的节点（非叶子节点）
    const expandIcons = page.locator('.el-tree-node__expand-icon:not(.is-leaf)');
    const count = await expandIcons.count();

    if (count > 0) {
      const firstIcon = expandIcons.first();

      // 获取父节点（树节点）- 通过 expand-icon 的父元素找到 tree-node
      const treeNode = firstIcon.locator('xpath=ancestor::div[contains(@class, "el-tree-node")]').first();

      // 使用 aria-expanded 判断展开/收起状态（比 class 字符串稳定）
      const ariaExpanded = await treeNode.getAttribute('aria-expanded').catch(() => null);
      const isExpanded = ariaExpanded === 'true';

      if (isExpanded) {
        // 如果已展开，先点击收起
        await firstIcon.click();
        await expect(treeNode).toHaveAttribute('aria-expanded', 'false');

        // 再次点击展开
        await firstIcon.click();
        await expect(treeNode).toHaveAttribute('aria-expanded', 'true');
      } else {
        // 如果未展开，直接点击展开
        await firstIcon.click();
        await expect(treeNode).toHaveAttribute('aria-expanded', 'true');
      }
    }
  });

  test('3. 新建部门', async () => {
    createdDepartment = {
      name: generateDepartmentName(),
      code: generateDepartmentCode()
    };

    // 点击部门树区域的“添加部门”（不是“新建组织”）
    await page.locator('button:has-text("添加部门")').first().click();

    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建部门');

    const dialog = page.locator('.el-dialog');
    await dialog.locator('input[placeholder*="部门名称"]').fill(createdDepartment.name);

    await dialog.locator('.el-dialog__footer button:has-text("确定")').click();

    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await expect(page.locator('.el-dialog')).not.toBeVisible();

    // 由于 WebKit 下 el-tree 可能保留了上一轮测试的展开状态，这里重新确保展开非叶子节点
    const expandIcons = page.locator('.el-tree-node__expand-icon:not(.is-leaf)');
    const iconCount = await expandIcons.count();
    for (let i = 0; i < iconCount; i++) {
      const icon = expandIcons.nth(i);
      const treeNode = icon.locator('xpath=ancestor::div[contains(@class, "el-tree-node")]').first();
      const aria = await treeNode.getAttribute('aria-expanded').catch(() => null);
      if (aria !== 'true') {
        await icon.click();
      }
    }

    // 新增部门后：树中应能找到该部门名称（只校验存在性，避免视口/滚动差异）
    const createdDeptNode = page
      .locator('.dept-name')
      .filter({ hasText: createdDepartment.name })
      .first();
    await expect(createdDeptNode).toHaveCount(1, { timeout: 20000 });
  });

  test('4. 编辑部门', async () => {
    // 使用树中第一个非叶子节点进行编辑测试
    await page.waitForSelector('.el-tree-node', { timeout: 10000 });
    const treeNodes = page.locator('.el-tree-node');
    const count = await treeNodes.count();

    if (count > 0) {
      // 使用第一个节点进行编辑
      const targetNode = treeNodes.first();

      // 右键点击节点打开菜单
      await targetNode.click({ button: 'right' });

      // 尝试点击编辑（如果菜单存在）
      const editMenuItem = page.locator('.el-dropdown-menu__item:has-text("编辑")');
      await editMenuItem.first().waitFor({ state: 'visible', timeout: 3000 }).catch(() => {});
      if (await editMenuItem.count() > 0) {
        await editMenuItem.click();
        await expect(page.locator('.el-dialog')).toBeVisible();
        await expect(page.locator('.el-dialog__title')).toContainText('编辑部门');

        updatedDepartmentName = generateDepartmentName();

        const dialog = page.locator('.el-dialog');
        const nameInput = dialog.locator('input[placeholder*="部门名称"]');
        await nameInput.clear();
        await nameInput.fill(updatedDepartmentName);

        await dialog.locator('.el-dialog__footer button:has-text("确定")').click();

        await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
        await expect(page.locator('.el-message--success').first()).toContainText('成功');
        await expect(page.locator('.el-dialog')).not.toBeVisible();

        // 编辑后：树中应能找到更新后的部门名称
        const updatedDeptNode = page
          .locator('.dept-name')
          .filter({ hasText: updatedDepartmentName })
          .first();
        await expect(updatedDeptNode).toBeVisible({ timeout: 10000 });
      }

    }
  });

  test('5. 删除部门', async () => {
    // 使用树中第一个节点进行删除测试
    await page.waitForSelector('.el-tree-node', { timeout: 10000 });
    const treeNodes = page.locator('.el-tree-node');
    const count = await treeNodes.count();

    if (count > 0) {
      // 使用第一个节点进行删除
      const targetNode = treeNodes.first();

      // 右键点击节点打开菜单
      await targetNode.click({ button: 'right' });

      // 尝试点击删除（如果菜单存在）
      const deleteMenuItem = page.locator('.el-dropdown-menu__item:has-text("删除")');
      await deleteMenuItem.first().waitFor({ state: 'visible', timeout: 3000 }).catch(() => {});
      if (await deleteMenuItem.count() > 0) {
        const deletedDeptName = await targetNode.locator('.dept-name').first().innerText();
        expect(deletedDeptName).toBeTruthy();
        await deleteMenuItem.click();

        await expect(page.locator('.el-message-box')).toBeVisible();
        await expect(page.locator('.el-message-box__message')).toContainText('删除');
        await page.locator('.el-message-box__btns button:has-text("确定")').click();

        await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
        await expect(page.locator('.el-message--success').first()).toContainText('成功');

        // 删除后：树中不应再包含被删除的部门名称
        const deletedDeptNodes = page.locator('.dept-name').filter({ hasText: deletedDeptName });
        await expect(deletedDeptNodes).toHaveCount(0, { timeout: 10000 });
      }
    }
  });
});

test.describe('组织架构页面 - 同步通讯录错误展示', () => {
  test('同步部分失败时应弹出可复制的错误详情', async ({ browser }) => {
    const context = await browser.newContext({
      storageState: 'playwright/.auth/user.json'
    });
    const page = await context.newPage();
    const errorText = "同步员工失败: (pymysql.err.DataError) (1406, \"Data too long for column 'id_card' at row 1\")";

    await page.route('**/api/v1/wechat-work/config/get**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          message: 'ok',
          msg_details: [],
          data: { is_bound: true, corp_id: 'ww-test' }
        })
      });
    });

    await page.route('**/api/v1/wechat-work/sync/manual', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'warning',
          message: '同步完成，但有失败',
          msg_details: [errorText],
          data: {
            success: false,
            created_count: 0,
            updated_count: 0,
            deleted_count: 0,
            errors: [errorText],
            duration_seconds: 1.2
          }
        })
      });
    });

    await navigateTo(page, ROUTES.ORGANIZATION);

    const syncButton = page.locator('button:has-text("同步通讯录")');
    await expect(syncButton).toBeEnabled({ timeout: 10000 });
    await syncButton.click();

    await expect(page.locator('.el-message-box')).toBeVisible();
    await page.locator('.el-message-box__btns button:has-text("确定")').click();

    const dialog = page.locator('.el-dialog').filter({ hasText: '同步完成，但有失败' });
    await expect(dialog).toBeVisible({ timeout: 10000 });
    await expect(dialog.locator('.sync-error-item')).toContainText('id_card');
    await expect(dialog.locator('button:has-text("复制错误信息")')).toBeVisible();

    await context.close();
  });
});
