/**
 * 角色管理页面 E2E 测试
 */
import { test, expect } from '@playwright/test';
import { loginAndNavigate } from './fixtures/auth.js';

test.describe.serial('角色管理页面 - 元素存在性验证', () => {
  
  test('页面标题和新建按钮存在', async ({ page }) => {
    await loginAndNavigate(page, '角色管理');
    
    // 验证页面元素
    await expect(page.locator('.page-header h2')).toContainText('角色管理');
    await expect(page.getByRole('button', { name: '新建' }).first()).toBeVisible();
  });

  test('角色表格存在', async ({ page }) => {
    await loginAndNavigate(page, '角色管理');
    
    // 验证表格
    await expect(page.locator('.el-table')).toBeVisible();
  });

  test('操作按钮存在', async ({ page }) => {
    await loginAndNavigate(page, '角色管理');
    
    // 验证操作按钮
    await expect(page.locator('button:has-text("编辑")').first()).toBeVisible();
    await expect(page.locator('button:has-text("删除")').first()).toBeVisible();
  });
});

test.describe.serial('角色管理页面 - 功能测试', () => {
  
  test('新建角色功能 - 打开对话框', async ({ page }) => {
    await loginAndNavigate(page, '角色管理');
    
    // 1. 点击新建角色按钮
    await page.getByRole('button', { name: '新建角色' }).click();
    
    // 2. 等待对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建角色');
    
    // 3. 验证表单字段存在
    await expect(page.locator('input[placeholder="如 admin, editor"]')).toBeVisible();
    await expect(page.locator('input[placeholder="如 管理员"]')).toBeVisible();
    await expect(page.locator('textarea[placeholder="角色描述（选填）"]')).toBeVisible();
    
    // 4. 点击取消关闭对话框
    await page.locator('.el-dialog__footer button:has-text("取消")').click();
    await page.waitForTimeout(1000);
  });

  test('编辑角色功能 - 打开对话框', async ({ page }) => {
    await loginAndNavigate(page, '角色管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个角色的编辑按钮并点击
    const firstEditButton = page.locator('.el-table__row').first().locator('button:has-text("编辑")');
    await firstEditButton.click();
    
    // 3. 等待编辑对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('编辑角色');
    
    // 4. 验证表单字段存在
    await expect(page.locator('input[placeholder="如 管理员"]')).toBeVisible();
    
    // 5. 点击取消关闭对话框
    await page.locator('.el-dialog__footer button:has-text("取消")').click();
    await page.waitForTimeout(1000);
  });

  test('权限分配功能 - 打开抽屉', async ({ page }) => {
    await loginAndNavigate(page, '角色管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个角色的权限按钮并点击
    const firstRow = page.locator('.el-table__row').first();
    const permButton = firstRow.locator('button:has-text("权限")');
    await permButton.click();
    
    // 3. 等待权限分配抽屉出现
    await expect(page.locator('.el-drawer')).toBeVisible();
    await expect(page.locator('.el-drawer__header')).toContainText('分配权限');
    
    // 4. 验证权限列表区域存在
    await expect(page.locator('.el-drawer__body')).toBeVisible();
    
    // 5. 点击取消关闭抽屉
    await page.locator('.drawer-footer button:has-text("取消")').click();
    await page.waitForTimeout(1000);
  });

  test('查看角色用户功能 - 打开对话框', async ({ page }) => {
    await loginAndNavigate(page, '角色管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个角色的用户按钮并点击
    const firstRow = page.locator('.el-table__row').first();
    const userButton = firstRow.locator('button:has-text("用户")');
    await userButton.click();
    
    // 3. 等待用户列表对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('关联用户');
    
    // 4. 验证用户表格存在
    await expect(page.locator('.el-dialog .el-table')).toBeVisible();
    
    // 5. 点击关闭按钮
    await page.locator('.el-dialog__footer button:has-text("关闭")').click();
    await page.waitForTimeout(1000);
  });

  test('删除角色功能 - 打开确认对话框', async ({ page }) => {
    await loginAndNavigate(page, '角色管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个非系统角色的删除按钮并点击
    const rows = page.locator('.el-table__row');
    const count = await rows.count();
    
    for (let i = 0; i < count; i++) {
      const row = rows.nth(i);
      const deleteButton = row.locator('button:has-text("删除")');
      
      // 检查删除按钮是否可用（非禁用状态）
      const isDisabled = await deleteButton.evaluate(el => el.disabled);
      
      if (!isDisabled) {
        await deleteButton.click();
        
        // 3. 等待确认对话框出现
        await expect(page.locator('.el-message-box')).toBeVisible();
        
        // 4. 点击取消
        await page.locator('.el-message-box__btns button:has-text("取消")').click();
        await page.waitForTimeout(1000);
        break;
      }
    }
  });
});
