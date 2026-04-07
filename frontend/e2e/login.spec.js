/**
 * 登录页面 E2E 测试
 */
import { test, expect } from '@playwright/test';

test.describe.serial('登录页面 - 元素存在性验证', () => {
  
  test('页面标题存在', async ({ page }) => {
    await page.goto('http://localhost:5200/login');
    
    // 验证页面标题
    await expect(page.locator('.login-header h1')).toBeVisible();
  });

  test('用户名输入框存在', async ({ page }) => {
    await page.goto('http://localhost:5200/login');
    
    // 验证用户名输入框
    await expect(page.locator('.login-form input[placeholder="用户名"]')).toBeVisible();
  });

  test('密码输入框存在', async ({ page }) => {
    await page.goto('http://localhost:5200/login');
    
    // 验证密码输入框
    await expect(page.locator('.login-form input[type="password"]')).toBeVisible();
  });

  test('登录按钮存在', async ({ page }) => {
    await page.goto('http://localhost:5200/login');
    
    // 验证登录按钮
    await expect(page.locator('.login-form button:has-text("登录")')).toBeVisible();
  });

  test('记住密码复选框存在', async ({ page }) => {
    await page.goto('http://localhost:5200/login');
    
    // 验证记住密码复选框
    await expect(page.locator('.el-checkbox')).toBeVisible();
  });

  test('忘记密码链接存在', async ({ page }) => {
    await page.goto('http://localhost:5200/login');
    
    // 验证忘记密码链接
    await expect(page.locator('a:has-text("忘记密码")')).toBeVisible();
  });
});
