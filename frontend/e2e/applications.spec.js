/**
 * 应用管理页面 E2E 测试
 */
import { test, expect } from '@playwright/test';
import { loginAndNavigate } from './fixtures/auth.js';

test.describe.serial('应用管理页面 - 元素存在性验证', () => {
  
  test('页面标题存在', async ({ page }) => {
    await loginAndNavigate(page, '应用管理');
    
    // 验证页面元素 - 使用更通用的选择器
    await expect(page.locator('h2').first()).toContainText('应用管理');
  });

  test('搜索和筛选区域元素存在', async ({ page }) => {
    await loginAndNavigate(page, '应用管理');
    
    // 验证搜索区域元素
    await expect(page.locator('.filter-form')).toBeVisible();
  });

  test('应用表格存在', async ({ page }) => {
    await loginAndNavigate(page, '应用管理');
    
    // 验证表格
    await expect(page.locator('.el-table')).toBeVisible();
  });
});

test.describe.serial('应用管理页面 - 功能测试', () => {
  
  test('新增应用功能', async ({ page }) => {
    await loginAndNavigate(page, '应用管理');
    
    // 1. 点击新建按钮
    await page.getByRole('button', { name: '新建应用' }).click();
    
    // 2. 等待对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('新建应用');
    
    // 3. 填写应用信息
    const timestamp = Date.now();
    const appName = `测试应用_${timestamp}`;
    const appCode = `test_app_${timestamp}`;
    
    await page.locator('input[placeholder="请输入应用名称"]').fill(appName);
    await page.locator('input[placeholder="字母、数字、下划线"]').fill(appCode);
    await page.locator('textarea[placeholder="请输入应用描述"]').fill('这是一个测试应用');
    
    // 4. 点击确认按钮
    await page.locator('.el-dialog__footer button:has-text("确认")').click();
    
    // 5. 验证创建成功 - 等待对话框关闭
    await page.waitForTimeout(2000);
    
    // 6. 验证新应用出现在列表中
    await expect(page.locator('.el-table')).toContainText(appName);
  });

  test('查询应用功能', async ({ page }) => {
    await loginAndNavigate(page, '应用管理');
    
    // 1. 在搜索框中输入关键词
    await page.locator('.filter-form input[placeholder*="搜索应用名称或编码"]').fill('测试');
    
    // 2. 点击搜索按钮
    await page.locator('.filter-form button:has-text("搜索")').click();
    
    // 3. 等待搜索结果加载
    await page.waitForTimeout(2000);
    
    // 4. 验证表格中有数据或显示空状态
    const hasData = await page.locator('.el-table__row').count() > 0;
    const hasEmptyState = await page.locator('.empty-state').count() > 0;
    expect(hasData || hasEmptyState).toBeTruthy();
  });

  test('修改应用功能', async ({ page }) => {
    await loginAndNavigate(page, '应用管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 找到第一个应用的编辑按钮并点击
    const firstEditButton = page.locator('.el-table__row').first().locator('button:has-text("编辑")');
    await firstEditButton.click();
    
    // 3. 等待编辑对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('编辑应用');
    
    // 4. 修改应用名称
    const timestamp = Date.now();
    const newAppName = `修改后的应用_${timestamp}`;
    
    const nameInput = page.locator('input[placeholder="请输入应用名称"]');
    await nameInput.clear();
    await nameInput.fill(newAppName);
    
    // 5. 点击确认按钮
    await page.locator('.el-dialog__footer button:has-text("确认")').click();
    
    // 6. 等待对话框关闭
    await page.waitForTimeout(2000);
    
    // 7. 验证修改成功
    await expect(page.locator('.el-table')).toContainText(newAppName);
  });

  test('删除应用功能', async ({ page }) => {
    await loginAndNavigate(page, '应用管理');
    
    // 1. 等待表格加载
    await page.waitForSelector('.el-table__row', { timeout: 10000 });
    
    // 2. 获取第一个应用的名称
    const firstRow = page.locator('.el-table__row').first();
    const appName = await firstRow.locator('.app-name').textContent();
    
    // 3. 找到第一个应用的删除按钮并点击
    const firstDeleteButton = firstRow.locator('button:has-text("删除")');
    await firstDeleteButton.click();
    
    // 4. 等待确认对话框出现
    await expect(page.locator('.el-message-box')).toBeVisible();
    
    // 5. 点击确认删除
    await page.locator('.el-message-box__btns button:has-text("确定")').click();
    
    // 6. 等待删除完成
    await page.waitForTimeout(2000);
    
    // 7. 验证删除成功 - 应用名称不再出现在列表中
    await expect(page.locator('.el-table')).not.toContainText(appName);
  });
});
