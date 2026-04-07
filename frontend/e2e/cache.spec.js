/**
 * 缓存管理页面 E2E 测试
 */
import { test, expect } from '@playwright/test';
import { loginAndNavigate } from './fixtures/auth.js';

test.describe.serial('缓存管理页面 - 元素存在性验证', () => {
  
  test('页面标题存在', async ({ page }) => {
    await loginAndNavigate(page, '缓存管理');
    
    // 验证页面标题 - 使用更通用的选择器
    await expect(page.locator('h2').first()).toContainText('缓存');
  });

  test('操作按钮存在', async ({ page }) => {
    await loginAndNavigate(page, '缓存管理');
    
    // 验证操作按钮
    await expect(page.getByRole('button', { name: '刷新' })).toBeVisible();
  });

  test('缓存统计区域存在', async ({ page }) => {
    await loginAndNavigate(page, '缓存管理');
    
    // 验证缓存统计区域
    await expect(page.locator('.el-card').first()).toBeVisible();
  });

  test('缓存表格存在', async ({ page }) => {
    await loginAndNavigate(page, '缓存管理');
    
    // 验证缓存表格
    await expect(page.locator('.el-table')).toBeVisible();
  });
});
