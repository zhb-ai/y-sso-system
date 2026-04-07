/**
 * 员工管理页面 E2E 测试
 */
import { test, expect } from '@playwright/test';
import { loginAndNavigate } from './fixtures/auth.js';

test.describe.serial('员工管理页面 - 元素存在性验证', () => {
  
  test('页面标题存在', async ({ page }) => {
    await loginAndNavigate(page, '员工管理');
    
    // 验证页面标题
    await expect(page.locator('.page-header h2')).toContainText('员工管理');
  });

  test('搜索区域元素存在', async ({ page }) => {
    await loginAndNavigate(page, '员工管理');
    
    // 验证搜索区域元素
    await expect(page.locator('.filter-form')).toBeVisible();
  });

  test('员工表格存在', async ({ page }) => {
    await loginAndNavigate(page, '员工管理');
    
    // 验证表格
    await expect(page.locator('.el-table')).toBeVisible();
  });

  test('操作按钮存在', async ({ page }) => {
    await loginAndNavigate(page, '员工管理');
    
    // 验证操作按钮
    await expect(page.getByRole('button', { name: '新建' }).first()).toBeVisible();
    await expect(page.locator('button:has-text("编辑")').first()).toBeVisible();
    await expect(page.locator('button:has-text("删除")').first()).toBeVisible();
  });

  test('分页组件存在', async ({ page }) => {
    await loginAndNavigate(page, '员工管理');
    
    // 验证分页
    await expect(page.locator('.el-pagination')).toBeVisible();
  });
});
