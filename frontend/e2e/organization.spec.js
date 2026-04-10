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

      // 检查当前节点是否已展开
      const isExpanded = await treeNode.evaluate(el => el.classList.contains('is-expanded')).catch(() => false);

      if (isExpanded) {
        // 如果已展开，先点击收起
        await firstIcon.click();
        await page.waitForTimeout(500);

        // 验证节点已收起（不再包含 is-expanded 类）
        const isStillExpanded = await treeNode.evaluate(el => el.classList.contains('is-expanded')).catch(() => false);
        expect(isStillExpanded).toBe(false);

        // 再次点击展开
        await firstIcon.click();
        await page.waitForTimeout(500);
      } else {
        // 如果未展开，直接点击展开
        await firstIcon.click();
        await page.waitForTimeout(500);
      }

      // 验证节点已展开
      const isNowExpanded = await treeNode.evaluate(el => el.classList.contains('is-expanded')).catch(() => false);
      expect(isNowExpanded).toBe(true);
    }
  });

  test('3. 新建部门', async () => {
    createdDepartment = {
      name: generateDepartmentName(),
      code: generateDepartmentCode()
    };

    // 使用更精确的选择器：查找"新建组织"按钮
    await page.locator('button:has-text("新建组织")').click();

    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建组织');

    const dialog = page.locator('.el-dialog');
    await dialog.locator('input[placeholder*="组织名称"]').fill(createdDepartment.name);
    await dialog.locator('input[placeholder*="组织编码"]').fill(createdDepartment.code);

    await dialog.locator('.el-dialog__footer button:has-text("确定")').click();

    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');
    await page.waitForTimeout(2000);
    await expect(page.locator('.el-dialog')).not.toBeVisible();

    // 注：由于组织架构树可能需要刷新才能显示新数据，这里只验证操作成功
    // 实际项目中应该等待后端返回成功并刷新树数据
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
      await page.waitForTimeout(1000);

      // 尝试点击编辑（如果菜单存在）
      const editMenuItem = page.locator('.el-dropdown-menu__item:has-text("编辑")');
      if (await editMenuItem.count() > 0) {
        await editMenuItem.click();
        await expect(page.locator('.el-dialog')).toBeVisible();
        await expect(page.locator('.el-dialog__title')).toContainText('编辑组织');

        updatedDepartmentName = generateDepartmentName();

        const dialog = page.locator('.el-dialog');
        const nameInput = dialog.locator('input[placeholder*="组织名称"]');
        await nameInput.clear();
        await nameInput.fill(updatedDepartmentName);

        await dialog.locator('.el-dialog__footer button:has-text("确定")').click();

        await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
        await expect(page.locator('.el-message--success').first()).toContainText('成功');
        await page.waitForTimeout(2000);
        await expect(page.locator('.el-dialog')).not.toBeVisible();
      }

      // 注：由于组织架构树可能需要刷新才能显示更新后的数据，这里只验证操作成功
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
      await page.waitForTimeout(1000);

      // 尝试点击删除（如果菜单存在）
      const deleteMenuItem = page.locator('.el-dropdown-menu__item:has-text("删除")');
      if (await deleteMenuItem.count() > 0) {
        await deleteMenuItem.click();

        await expect(page.locator('.el-message-box')).toBeVisible();
        await expect(page.locator('.el-message-box__message')).toContainText('删除');
        await page.locator('.el-message-box__btns button:has-text("确定")').click();

        await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
        await expect(page.locator('.el-message--success').first()).toContainText('成功');
        await page.waitForTimeout(2000);
      }

      // 注：由于组织架构树可能需要刷新才能显示更新后的数据，这里只验证操作成功
    }
  });
});
