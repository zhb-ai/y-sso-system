/**
 * 系统设置页面 E2E 测试
 */
import { test, expect } from '@playwright/test';
import { loginAndNavigate } from './fixtures/auth.js';

test.describe.serial('系统设置页面 - 元素存在性验证', () => {
  
  test('页面标题存在', async ({ page }) => {
    await loginAndNavigate(page, '系统设置');
    
    // 验证页面标题
    await expect(page.locator('.page-header h2')).toContainText('系统设置');
  });

  test('设置卡片和表单存在', async ({ page }) => {
    await loginAndNavigate(page, '系统设置');
    
    // 验证设置卡片和表单
    await expect(page.locator('.el-card').first()).toBeVisible();
    await expect(page.locator('.el-form').first()).toBeVisible();
  });

  test('保存按钮存在', async ({ page }) => {
    await loginAndNavigate(page, '系统设置');
    
    // 验证保存按钮
    await expect(page.getByRole('button', { name: '保存' })).toBeVisible();
  });
});
