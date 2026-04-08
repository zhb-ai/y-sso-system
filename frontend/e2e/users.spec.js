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

test.describe.serial('用户管理页面 - 功能测试', () => {
  
  test('新建用户功能 - 打开对话框', async ({ page }) => {
    await loginAndNavigate(page, '用户管理');
    
    // 1. 点击新建用户按钮
    await page.getByRole('button', { name: '新建用户' }).click();
    
    // 2. 等待对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建用户');
    
    // 3. 验证表单字段存在
    await expect(page.locator('input[placeholder="请输入用户名"]')).toBeVisible();
    await expect(page.locator('input[placeholder="请输入姓名"]')).toBeVisible();
    await expect(page.locator('input[placeholder="请输入手机号"]')).toBeVisible();
    await expect(page.locator('input[placeholder="请输入初始密码"]')).toBeVisible();
    
    // 4. 点击取消关闭对话框
    await page.locator('.el-dialog__footer button:has-text("取消")').click();
    await page.waitForTimeout(1000);
  });

  test('查询用户功能', async ({ page }) => {
    await loginAndNavigate(page, '用户管理');
    
    // 1. 在搜索框中输入关键词
    await page.locator('.filter-form input[placeholder*="请输入用户名、姓名或邮箱"]').fill('admin');
    
    // 2. 点击搜索按钮
    await page.locator('.filter-form button:has-text("搜索")').click();
    
    // 3. 等待搜索结果加载
    await page.waitForTimeout(2000);
    
    // 4. 验证表格中有数据或显示空状态
    const hasData = await page.locator('.el-table__row').count() > 0;
    const hasEmptyState = await page.locator('.empty-state').count() > 0;
    expect(hasData || hasEmptyState).toBeTruthy();
  });

  test('编辑用户功能', async ({ page }) => {
    await loginAndNavigate(page, '用户管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个用户的编辑按钮并点击
    const firstEditButton = page.locator('.el-table__row').first().locator('button:has-text("编辑")');
    await firstEditButton.click();
    
    // 3. 等待编辑对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('编辑用户');
    
    // 4. 修改用户姓名
    const timestamp = Date.now();
    const newName = `修改后的用户_${timestamp}`;
    
    const nameInput = page.locator('input[placeholder="请输入姓名"]');
    await nameInput.clear();
    await nameInput.fill(newName);
    
    // 5. 点击确认按钮
    await page.locator('.el-dialog__footer button:has-text("确定")').click();
    
    // 6. 等待对话框关闭
    await page.waitForTimeout(2000);
    
    // 7. 验证修改成功
    await expect(page.locator('.el-table')).toContainText(newName);
  });

  test('禁用用户功能', async ({ page }) => {
    await loginAndNavigate(page, '用户管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个启用的用户的禁用按钮并点击（红色按钮）
    const firstRow = page.locator('.el-table__row').first();
    const disableButton = firstRow.locator('button.el-button--danger:has-text("禁用")');
    
    // 如果存在禁用按钮则点击
    if (await disableButton.count() > 0) {
      await disableButton.click();
      
      // 3. 等待确认对话框出现
      await expect(page.locator('.el-message-box')).toBeVisible();
      
      // 4. 点击确认
      await page.locator('.el-message-box__btns button:has-text("确定")').click();
      
      // 5. 等待操作完成
      await page.waitForTimeout(2000);
      
      // 6. 验证状态变为禁用
      await expect(firstRow.locator('.el-tag--danger')).toContainText('禁用');
    }
  });

  test('启用用户功能', async ({ page }) => {
    await loginAndNavigate(page, '用户管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个禁用的用户的启用按钮并点击（绿色按钮）
    const firstRow = page.locator('.el-table__row').first();
    const enableButton = firstRow.locator('button.el-button--success:has-text("启用")');
    
    // 如果存在启用按钮则点击
    if (await enableButton.count() > 0) {
      await enableButton.click();
      
      // 3. 等待确认对话框出现
      await expect(page.locator('.el-message-box')).toBeVisible();
      
      // 4. 点击确认
      await page.locator('.el-message-box__btns button:has-text("确定")').click();
      
      // 5. 等待操作完成
      await page.waitForTimeout(2000);
      
      // 6. 验证状态变为启用
      await expect(firstRow.locator('.el-tag--success')).toContainText('启用');
    }
  });

  test('重置密码功能', async ({ page }) => {
    await loginAndNavigate(page, '用户管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个用户的重置密码按钮并点击
    const firstRow = page.locator('.el-table__row').first();
    const resetButton = firstRow.locator('button:has-text("重置密码")');
    await resetButton.click();
    
    // 3. 等待确认对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('重置密码');
    
    // 4. 点击确认重置
    await page.locator('.el-dialog__footer button:has-text("确定重置")').click();
    
    // 5. 等待结果对话框出现
    await page.waitForTimeout(2000);
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('密码已重置');
    
    // 6. 关闭对话框
    await page.locator('.el-dialog__headerbtn').click();
  });

  test('分配角色功能', async ({ page }) => {
    await loginAndNavigate(page, '用户管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个用户的角色按钮并点击
    const firstRow = page.locator('.el-table__row').first();
    const roleButton = firstRow.locator('button:has-text("角色")');
    await roleButton.click();
    
    // 3. 等待角色分配对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('分配角色');
    
    // 4. 验证角色选择区域存在
    await expect(page.locator('.el-checkbox-group')).toBeVisible();
    
    // 5. 点击取消关闭对话框
    await page.locator('.el-dialog__footer button:has-text("取消")').click();
  });

  test('分配SSO角色功能', async ({ page }) => {
    await loginAndNavigate(page, '用户管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个用户的SSO按钮并点击
    const firstRow = page.locator('.el-table__row').first();
    const ssoButton = firstRow.locator('button:has-text("SSO")');
    await ssoButton.click();
    
    // 3. 等待SSO角色分配对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('分配 SSO 角色');
    
    // 4. 验证SSO角色选择区域存在
    await expect(page.locator('.el-checkbox-group')).toBeVisible();
    
    // 5. 点击取消关闭对话框
    await page.locator('.el-dialog__footer button:has-text("取消")').click();
  });
});
