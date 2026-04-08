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

test.describe.serial('员工管理页面 - 功能测试', () => {
  
  test('新建员工功能 - 打开对话框', async ({ page }) => {
    await loginAndNavigate(page, '员工管理');
    
    // 1. 点击新建员工按钮
    await page.getByRole('button', { name: '新建员工' }).click();
    
    // 2. 等待对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建员工');
    
    // 3. 验证表单字段存在
    await expect(page.locator('input[placeholder="请输入姓名"]')).toBeVisible();
    await expect(page.locator('input[placeholder="请输入员工编码"]')).toBeVisible();
    await expect(page.locator('input[placeholder="请输入手机号"]')).toBeVisible();
    await expect(page.locator('input[placeholder="请输入邮箱"]')).toBeVisible();
    
    // 4. 验证性别单选框存在
    await expect(page.locator('.el-radio-group')).toBeVisible();
    
    // 5. 点击取消关闭对话框
    await page.locator('.el-dialog__footer button:has-text("取消")').click();
    await page.waitForTimeout(1000);
  });

  test('查询员工功能', async ({ page }) => {
    await loginAndNavigate(page, '员工管理');
    
    // 1. 在搜索框输入关键词
    const searchInput = page.locator('.filter-form input[placeholder="姓名/手机号"]');
    await searchInput.fill('测试');
    
    // 2. 点击搜索按钮
    await page.locator('.filter-form button:has-text("搜索")').click();
    
    // 3. 等待搜索完成
    await page.waitForTimeout(2000);
    
    // 4. 验证表格仍然可见
    await expect(page.locator('.el-table')).toBeVisible();
    
    // 5. 点击重置按钮
    await page.locator('.filter-form button:has-text("重置")').click();
    await page.waitForTimeout(1000);
  });

  test('编辑员工功能 - 打开对话框', async ({ page }) => {
    await loginAndNavigate(page, '员工管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个员工的编辑按钮并点击
    const firstRow = page.locator('.el-table__row').first();
    const editButton = firstRow.locator('button:has-text("编辑")');
    await editButton.click();
    
    // 3. 等待编辑对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('编辑员工');
    
    // 4. 验证表单字段存在（编辑时有标签页）
    await expect(page.locator('.el-tabs')).toBeVisible();
    await expect(page.locator('.el-tabs__item:has-text("用户账号")')).toBeVisible();
    await expect(page.locator('.el-tabs__item:has-text("组织管理")')).toBeVisible();
    await expect(page.locator('.el-tabs__item:has-text("部门管理")')).toBeVisible();
    
    // 5. 点击取消关闭对话框
    await page.locator('.el-dialog__footer button:has-text("取消")').click();
    await page.waitForTimeout(1000);
  });

  test('删除员工功能 - 打开确认对话框', async ({ page }) => {
    await loginAndNavigate(page, '员工管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个员工的删除按钮并点击
    const firstRow = page.locator('.el-table__row').first();
    const deleteButton = firstRow.locator('button:has-text("删除")');
    await deleteButton.click();
    
    // 3. 等待确认对话框出现
    await expect(page.locator('.el-message-box')).toBeVisible();
    
    // 4. 点击取消
    await page.locator('.el-message-box__btns button:has-text("取消")').click();
    await page.waitForTimeout(1000);
  });

  test('组织管理功能 - 打开对话框', async ({ page }) => {
    await loginAndNavigate(page, '员工管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个员工的组织按钮并点击
    const firstRow = page.locator('.el-table__row').first();
    const orgButton = firstRow.locator('button:has-text("组织")');
    await orgButton.click();
    
    // 3. 等待组织管理对话框出现（独立的对话框）
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('管理员工组织');
    
    // 4. 验证组织管理内容存在
    await expect(page.locator('.el-dialog__body')).toBeVisible();
    
    // 5. 点击关闭按钮
    await page.locator('.el-dialog__headerbtn').click();
    await page.waitForTimeout(1000);
  });

  test('部门管理功能 - 打开对话框', async ({ page }) => {
    await loginAndNavigate(page, '员工管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个员工的部门按钮并点击
    const firstRow = page.locator('.el-table__row').first();
    const deptButton = firstRow.locator('button:has-text("部门")');
    await deptButton.click();
    
    // 3. 等待部门管理对话框出现（独立的对话框）
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('管理员工部门');
    
    // 4. 验证部门管理内容存在
    await expect(page.locator('.el-dialog__body')).toBeVisible();
    
    // 5. 点击关闭按钮
    await page.locator('.el-dialog__headerbtn').click();
    await page.waitForTimeout(1000);
  });
});
