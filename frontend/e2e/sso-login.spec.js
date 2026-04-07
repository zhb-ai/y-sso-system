/**
 * 单点登录页面 E2E 测试
 */
import { test, expect } from '@playwright/test';
import { login } from './fixtures/auth.js';

test.describe.serial('单点登录页面 - 元素存在性验证', () => {
  
  test('页面标题存在', async ({ page }) => {
    await page.goto('http://localhost:5200/sso/login');
    
    // 验证页面标题
    await expect(page.locator('.login-header h1')).toBeVisible();
  });

  test('用户名输入框存在', async ({ page }) => {
    await page.goto('http://localhost:5200/sso/login');
    
    // 验证用户名输入框
    await expect(page.locator('.login-form input[placeholder*="用户名"]')).toBeVisible();
  });

  test('密码输入框存在', async ({ page }) => {
    await page.goto('http://localhost:5200/sso/login');
    
    // 验证密码输入框
    await expect(page.locator('.login-form input[type="password"]')).toBeVisible();
  });

  test('登录按钮存在', async ({ page }) => {
    await page.goto('http://localhost:5200/sso/login');
    
    // 验证登录按钮 - 使用更通用的选择器
    await expect(page.locator('.login-form button').first()).toBeVisible();
  });

  test('已登录时显示用户信息', async ({ page }) => {
    // 先登录
    await login(page);
    
    // 访问SSO登录页
    await page.goto('http://localhost:5200/sso/login');
    await page.waitForTimeout(2000);
    
    // 验证显示用户信息 - 使用更通用的选择器
    await expect(page.locator('.sso-username, .sso-user-info, .sso-user-detail').first()).toBeVisible();
  });

  test('已登录时显示进入管理后台链接', async ({ page }) => {
    // 先登录
    await login(page);
    
    // 访问SSO登录页
    await page.goto('http://localhost:5200/sso/login');
    await page.waitForTimeout(2000);
    
    // 验证显示进入管理后台链接
    await expect(page.locator('a:has-text("进入管理后台")')).toBeVisible();
  });
});
