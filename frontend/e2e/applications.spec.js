/**
 * 应用管理页面 E2E 测试
 */
import { test, expect } from '@playwright/test';
import { loginAndNavigate } from './fixtures/auth.js';

test.describe.serial('应用管理页面 - 元素存在性验证', () => {
  
  test('页面标题存在', async ({ page }) => {
    await loginAndNavigate(page, '应用管理');
    
    // 验证页面元素 - 使用更通用的选择器
    await expect(page.locator('h2').first()).toContainText('应用管理');
  });

  test('搜索和筛选区域元素存在', async ({ page }) => {
    await loginAndNavigate(page, '应用管理');
    
    // 验证搜索区域元素
    await expect(page.locator('.filter-form')).toBeVisible();
  });

  test('应用表格存在', async ({ page }) => {
    await loginAndNavigate(page, '应用管理');
    
    // 验证表格
    await expect(page.locator('.el-table')).toBeVisible();
  });
});
