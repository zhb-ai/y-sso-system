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

test.describe.serial('组织架构页面 - 功能测试', () => {
  
  test('新建员工功能 - 打开对话框', async ({ page }) => {
    await loginAndNavigate(page, '组织架构');
    
    // 1. 点击新建员工按钮
    await page.getByRole('button', { name: '新建员工' }).click();
    
    // 2. 等待对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建员工');
    
    // 3. 验证表单字段存在
    await expect(page.locator('input[placeholder="请输入姓名"]')).toBeVisible();
    await expect(page.locator('input[placeholder="请输入员工编号"]')).toBeVisible();
    await expect(page.locator('input[placeholder="请输入手机号"]')).toBeVisible();
    
    // 4. 点击取消关闭对话框
    await page.locator('.el-dialog__footer button:has-text("取消")').click();
    await page.waitForTimeout(1000);
  });

  test('新建组织功能 - 打开对话框', async ({ page }) => {
    await loginAndNavigate(page, '组织架构');
    
    // 1. 点击新建组织按钮
    await page.getByRole('button', { name: '新建组织' }).click();
    
    // 2. 等待对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建组织');
    
    // 3. 验证表单字段存在
    await expect(page.locator('input[placeholder="请输入组织名称"]')).toBeVisible();
    await expect(page.locator('input[placeholder="请输入组织编码"]')).toBeVisible();
    
    // 4. 点击取消关闭对话框
    await page.locator('.el-dialog__footer button:has-text("取消")').click();
    await page.waitForTimeout(1000);
  });

  test('切换组织功能 - 组织选择器存在', async ({ page }) => {
    await loginAndNavigate(page, '组织架构');
    
    // 1. 验证组织选择器存在
    await expect(page.locator('.filter-form .el-select')).toBeVisible();
    
    // 2. 点击组织选择器
    await page.locator('.filter-form .el-select').click();
    await page.waitForTimeout(1000);
    
    // 3. 验证下拉选项存在
    await expect(page.locator('.el-select-dropdown')).toBeVisible();
    
    // 4. 按ESC关闭下拉
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
  });

  test('编辑组织功能 - 打开对话框', async ({ page }) => {
    await loginAndNavigate(page, '组织架构');
    
    // 1. 点击编辑组织按钮
    const editOrgButton = page.locator('button:has-text("编辑组织")');
    if (await editOrgButton.count() > 0) {
      await editOrgButton.click();
      
      // 2. 等待对话框出现
      await expect(page.locator('.el-dialog')).toBeVisible();
      await expect(page.locator('.el-dialog__title')).toContainText('编辑组织');
      
      // 3. 验证表单字段存在
      await expect(page.locator('input[placeholder="请输入组织名称"]')).toBeVisible();
      
      // 4. 点击取消关闭对话框
      await page.locator('.el-dialog__footer button:has-text("取消")').click();
      await page.waitForTimeout(1000);
    }
  });

  test('绑定企业微信功能 - 按钮存在', async ({ page }) => {
    await loginAndNavigate(page, '组织架构');
    
    // 验证绑定企业微信按钮或已绑定状态存在
    const bindButton = page.locator('button:has-text("绑定企业微信")');
    const unbindButton = page.locator('button:has-text("解绑")');
    
    const hasBindButton = await bindButton.count() > 0;
    const hasUnbindButton = await unbindButton.count() > 0;
    
    expect(hasBindButton || hasUnbindButton).toBeTruthy();
  });

  test('同步通讯录功能 - 按钮存在', async ({ page }) => {
    await loginAndNavigate(page, '组织架构');
    
    // 验证同步通讯录按钮存在（可能被禁用）
    const syncButton = page.locator('button:has-text("同步通讯录")');
    await expect(syncButton).toBeVisible();
  });

  test('添加部门功能 - 打开对话框', async ({ page }) => {
    await loginAndNavigate(page, '组织架构');
    
    // 1. 点击添加部门按钮（部门卡片头部）
    const addDeptButton = page.locator('.dept-card-header button:has-text("添加部门")');
    await addDeptButton.click();
    
    // 2. 等待对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建部门');
    
    // 3. 验证表单字段存在
    await expect(page.locator('input[placeholder="请输入部门名称"]')).toBeVisible();
    
    // 4. 点击取消关闭对话框
    await page.locator('.el-dialog__footer button:has-text("取消")').click();
    await page.waitForTimeout(1000);
  });

  test('部门树操作按钮存在', async ({ page }) => {
    await loginAndNavigate(page, '组织架构');
    
    // 1. 等待部门树加载
    await page.waitForSelector('.el-tree-node', { timeout: 10000 });
    
    // 2. 验证第一个部门节点的操作按钮存在（使用first()解决多个元素问题）
    await expect(page.locator('.dept-actions').first()).toBeVisible();
  });

  test('添加员工到部门功能 - 按钮存在', async ({ page }) => {
    await loginAndNavigate(page, '组织架构');
    
    // 1. 等待部门树加载
    await page.waitForSelector('.el-tree-node', { timeout: 10000 });
    
    // 2. 点击第一个部门
    const firstDept = page.locator('.el-tree-node').first();
    await firstDept.click();
    await page.waitForTimeout(1000);
    
    // 3. 验证添加员工到部门按钮存在
    const addEmpButton = page.locator('button:has-text("添加员工到部门")');
    await expect(addEmpButton).toBeVisible();
  });
});
