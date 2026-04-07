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
