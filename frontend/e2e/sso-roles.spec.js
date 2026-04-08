/**
 * SSO角色管理页面 E2E 测试
 */
import { test, expect } from '@playwright/test';
import { loginAndNavigate } from './fixtures/auth.js';

test.describe.serial('SSO角色管理页面 - 元素存在性验证', () => {
  
  test('页面标题和新建按钮存在', async ({ page }) => {
    await loginAndNavigate(page, 'SSO 角色');
    
    // 验证页面元素
    await expect(page.locator('.page-header h2')).toContainText('SSO');
    await expect(page.getByRole('button', { name: '新建' }).first()).toBeVisible();
  });

  test('搜索区域元素存在', async ({ page }) => {
    await loginAndNavigate(page, 'SSO 角色');
    
    // 验证搜索区域元素
    await expect(page.locator('.filter-form')).toBeVisible();
  });

  test('角色表格存在', async ({ page }) => {
    await loginAndNavigate(page, 'SSO 角色');
    
    // 验证表格
    await expect(page.locator('.el-table')).toBeVisible();
  });

  test('操作按钮存在', async ({ page }) => {
    await loginAndNavigate(page, 'SSO 角色');
    
    // 验证操作按钮
    await expect(page.locator('button:has-text("编辑")').first()).toBeVisible();
    await expect(page.locator('button:has-text("删除")').first()).toBeVisible();
  });
});

test.describe.serial('SSO角色管理页面 - 功能测试', () => {
  
  test('新建SSO角色功能 - 打开对话框', async ({ page }) => {
    await loginAndNavigate(page, 'SSO 角色');
    
    // 1. 点击新建SSO角色按钮
    await page.getByRole('button', { name: '新建 SSO 角色' }).click();
    
    // 2. 等待对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建 SSO 角色');
    
    // 3. 验证表单字段存在
    await expect(page.locator('input[placeholder="如 finance_admin, hr_viewer"]')).toBeVisible();
    await expect(page.locator('input[placeholder="如 财务管理员"]')).toBeVisible();
    await expect(page.locator('textarea[placeholder="角色描述（选填）"]')).toBeVisible();
    await expect(page.locator('.el-input-number')).toBeVisible();
    
    // 4. 点击取消关闭对话框
    await page.locator('.el-dialog__footer button:has-text("取消")').click();
    await page.waitForTimeout(1000);
  });

  test('编辑SSO角色功能 - 打开对话框', async ({ page }) => {
    await loginAndNavigate(page, 'SSO 角色');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个SSO角色的编辑按钮并点击
    const firstEditButton = page.locator('.el-table__row').first().locator('button:has-text("编辑")');
    await firstEditButton.click();
    
    // 3. 等待编辑对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('编辑 SSO 角色');
    
    // 4. 验证表单字段存在（编辑时有状态开关）
    await expect(page.locator('input[placeholder="如 财务管理员"]')).toBeVisible();
    await expect(page.locator('.el-switch')).toBeVisible();
    
    // 5. 点击取消关闭对话框
    await page.locator('.el-dialog__footer button:has-text("取消")').click();
    await page.waitForTimeout(1000);
  });

  test('删除SSO角色功能 - 打开确认对话框', async ({ page }) => {
    await loginAndNavigate(page, 'SSO 角色');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个SSO角色的删除按钮并点击
    const firstRow = page.locator('.el-table__row').first();
    const deleteButton = firstRow.locator('button:has-text("删除")');
    await deleteButton.click();
    
    // 3. 等待确认对话框出现
    await expect(page.locator('.el-message-box')).toBeVisible();
    
    // 4. 点击取消
    await page.locator('.el-message-box__btns button:has-text("取消")').click();
    await page.waitForTimeout(1000);
  });
});
