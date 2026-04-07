/**
 * 组织架构页面 E2E 测试
 */
import { test, expect } from '@playwright/test';
import { loginAndNavigate } from './fixtures/auth.js';

test.describe.serial('组织架构页面 - 元素存在性验证', () => {
  
  test('页面标题存在', async ({ page }) => {
    await loginAndNavigate(page, '组织架构');
    
    // 验证页面标题
    await expect(page.locator('.page-header h2')).toContainText('组织架构');
  });

  test('操作按钮存在', async ({ page }) => {
    await loginAndNavigate(page, '组织架构');
    
    // 验证操作按钮
    await expect(page.getByRole('button', { name: '新建' }).first()).toBeVisible();
  });

  test('部门树存在', async ({ page }) => {
    await loginAndNavigate(page, '组织架构');
    
    // 验证部门树
    await expect(page.locator('.el-tree')).toBeVisible();
  });
});
