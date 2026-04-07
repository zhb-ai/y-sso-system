/**
 * 仪表盘页面 E2E 测试
 */
import { test, expect } from '@playwright/test';
import { loginAndNavigate } from './fixtures/auth.js';

// 使用串行模式，避免登录状态冲突
test.describe.serial('仪表盘页面 - 元素存在性验证', () => {
  
  test('页面标题和欢迎语显示正确', async ({ page }) => {
    await loginAndNavigate(page, '仪表盘');
    
    // 验证页面元素 - 使用更通用的选择器
    await expect(page.locator('.page-header h2')).toContainText('仪表盘');
    await expect(page.locator('.page-header h5')).toContainText('欢迎回来');
  });

  test('统计卡片存在', async ({ page }) => {
    await loginAndNavigate(page, '仪表盘');
    
    // 验证统计卡片
    await expect(page.locator('.stats-cards')).toBeVisible();
  });

  test('搜索区域元素存在', async ({ page }) => {
    await loginAndNavigate(page, '仪表盘');
    
    // 验证搜索区域元素
    await expect(page.locator('.filter-form')).toBeVisible();
  });

  test('登录记录表格和分页存在', async ({ page }) => {
    await loginAndNavigate(page, '仪表盘');
    
    // 验证表格和分页
    await expect(page.locator('.el-table')).toBeVisible();
    await expect(page.locator('.el-pagination')).toBeVisible();
  });
});
