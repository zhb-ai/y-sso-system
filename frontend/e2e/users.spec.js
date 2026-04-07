/**
 * 用户管理页面 E2E 测试
 */
import { test, expect } from '@playwright/test';
import { loginAndNavigate } from './fixtures/auth.js';

test.describe.serial('用户管理页面 - 元素存在性验证', () => {
  
  test('页面标题和新建按钮存在', async ({ page }) => {
    await loginAndNavigate(page, '用户管理');
    
    // 验证页面元素
    await expect(page.locator('.page-header h2')).toContainText('用户管理');
    await expect(page.getByRole('button', { name: '新建' }).first()).toBeVisible();
  });

  test('搜索和筛选区域元素存在', async ({ page }) => {
    await loginAndNavigate(page, '用户管理');
    
    // 验证搜索区域元素
    await expect(page.locator('.filter-form')).toBeVisible();
  });

  test('用户表格存在', async ({ page }) => {
    await loginAndNavigate(page, '用户管理');
    
    // 验证表格
    await expect(page.locator('.el-table')).toBeVisible();
  });

  test('表格列标题存在', async ({ page }) => {
    await loginAndNavigate(page, '用户管理');
    
    // 验证表格列标题
    await expect(page.locator('.el-table__header')).toBeVisible();
  });

  test('分页组件存在', async ({ page }) => {
    await loginAndNavigate(page, '用户管理');
    
    // 验证分页
    await expect(page.locator('.el-pagination')).toBeVisible();
  });
});
