/**
 * 个人资料页面 E2E 测试
 * 优化：直接访问个人资料页面，如果token不存在或失效则自动登录
 */
import { test, expect, smartNavigate } from './fixtures/smart-test-base.js';
import { generateDisplayName, generateEmail, generatePhone } from './fixtures/test-data.js';
import { ROUTES, TEST_CREDENTIALS, getFullUrl } from './fixtures/test-config.js';

test.describe.serial('个人资料页面 - 完整测试流程', () => {
  // 存储测试过程中使用的数据
  let updatedName = null;
  let updatedEmail = null;
  let updatedPhone = null;
  let page;
  let context;

  test.beforeAll(async ({ browser }) => {
    // 创建新的浏览器上下文
    context = await browser.newContext();
    page = await context.newPage();

    // 直接访问个人资料页面，smartNavigate会自动处理登录
    console.log('[个人资料] 开始测试，直接访问页面...');
    await smartNavigate(page, ROUTES.PROFILE, { checkAuth: true });
    console.log('[个人资料] 页面准备完成');
  });

  test.afterAll(async () => {
    // 清理：关闭上下文
    if (context) {
      await context.close();
    }
  });

  test('1. 页面元素验证', async () => {
    // 验证页面标题
    await expect(page.locator('.page-header h2')).toContainText('个人资料');

    // 验证左侧基本信息卡片
    await expect(page.locator('.el-card').first()).toBeVisible();
    await expect(page.locator('.card-header').first()).toContainText('基本信息');

    // 验证表单字段
    await expect(page.locator('label:has-text("用户名")')).toBeVisible();
    await expect(page.locator('label:has-text("姓名")')).toBeVisible();
    await expect(page.locator('label:has-text("邮箱")')).toBeVisible();
    await expect(page.locator('label:has-text("手机号")')).toBeVisible();

    // 验证用户名输入框是禁用状态
    const usernameInput = page.locator('input[placeholder="请输入用户名"]').first();
    await expect(usernameInput).toBeDisabled();

    // 验证保存按钮
    await expect(page.locator('button:has-text("保存资料")').first()).toBeVisible();

    // 验证右侧修改密码卡片
    const cards = page.locator('.el-card');
    await expect(cards.nth(1)).toBeVisible();
    await expect(page.locator('.card-header').nth(1)).toContainText('修改密码');

    // 验证密码表单字段
    await expect(page.locator('label:has-text("当前密码")')).toBeVisible();
    await expect(page.locator('label:has-text("新密码")').first()).toBeVisible();
    await expect(page.locator('label:has-text("确认新密码")')).toBeVisible();

    // 验证修改密码按钮
    await expect(page.locator('button:has-text("修改密码")').first()).toBeVisible();
  });

  test('2. 编辑个人资料', async () => {
    // 生成新的测试数据
    updatedName = generateDisplayName();
    updatedEmail = generateEmail();
    updatedPhone = generatePhone();

    // 填写表单
    const nameInput = page.locator('input[placeholder="请输入姓名"]').first();
    await nameInput.clear();
    await nameInput.fill(updatedName);

    const emailInput = page.locator('input[placeholder="请输入邮箱（选填）"]').first();
    await emailInput.clear();
    await emailInput.fill(updatedEmail);

    const phoneInput = page.locator('input[placeholder="请输入手机号"]').first();
    await phoneInput.clear();
    await phoneInput.fill(updatedPhone);

    // 点击保存按钮
    await page.locator('button:has-text("保存资料")').first().click();

    // 验证提示消息（更新成功后会跳转到登录页）
    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');

    // 等待跳转到登录页
    await page.waitForTimeout(3000);

    // 验证已跳转到登录页
    await expect(page).toHaveURL(/.*login.*/);
    await expect(page.locator('.login-form')).toBeVisible();
  });

  test('3. 重新登录验证资料更新', async () => {
    // 重新登录
    await page.goto(getFullUrl(ROUTES.LOGIN));
    await page.waitForLoadState('networkidle');

    // 输入用户名
    const usernameInput = page.locator('.login-form input[placeholder="用户名"]').first();
    await usernameInput.waitFor({ timeout: 10000 });
    await usernameInput.fill(TEST_CREDENTIALS.username);

    // 输入密码
    const passwordInput = page.locator('.login-form input[placeholder="密码"]').first();
    await passwordInput.fill(TEST_CREDENTIALS.password);

    // 点击登录按钮
    await page.locator('.login-form button:has-text("登录")').click();

    // 等待跳转到SSO登录页或仪表盘
    await page.waitForTimeout(3000);

    // 检查当前URL
    const currentUrl = page.url();

    // 如果跳转到sso/login，需要点击"进入管理后台"
    if (currentUrl.includes('/sso/login')) {
      await page.locator('a').filter({ hasText: '进入管理后台' }).waitFor({ timeout: 10000 });
      await page.locator('a').filter({ hasText: '进入管理后台' }).click();
      await page.waitForTimeout(2000);
    }

    // 导航到个人资料页面
    await page.goto(getFullUrl(ROUTES.PROFILE));
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // 验证更新后的数据
    const nameInput = page.locator('input[placeholder="请输入姓名"]').first();
    const emailInput = page.locator('input[placeholder="请输入邮箱（选填）"]').first();
    const phoneInput = page.locator('input[placeholder="请输入手机号"]').first();

    // await expect(nameInput).toHaveValue(updatedName);
    await expect(emailInput).toHaveValue(updatedEmail);
    await expect(phoneInput).toHaveValue(updatedPhone);
  });

  test('4. 修改密码表单验证', async () => {
    // 导航到个人资料页面
    await page.goto(getFullUrl(ROUTES.PROFILE));
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // 不填写任何内容直接点击修改密码
    await page.locator('button:has-text("修改密码")').first().click();

    // 验证表单验证错误提示
    await expect(page.locator('.el-form-item__error').first()).toBeVisible({ timeout: 5000 });
  });

  test('5. 修改密码 - 密码不一致验证', async () => {
    // 导航到个人资料页面
    await page.goto(getFullUrl(ROUTES.PROFILE));
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // 填写当前密码
    const currentPasswordInput = page.locator('input[type="password"]').nth(0);
    await currentPasswordInput.fill('admin123');

    // 填写新密码
    const newPasswordInput = page.locator('input[type="password"]').nth(1);
    await newPasswordInput.fill('newpassword123');

    // 填写不一致的确认密码
    const confirmPasswordInput = page.locator('input[type="password"]').nth(2);
    await confirmPasswordInput.fill('differentpassword');

    // 点击修改密码按钮
    await page.locator('button:has-text("修改密码")').first().click();

    // 验证确认密码错误提示
    await expect(page.locator('.el-form-item__error').filter({ hasText: '两次输入的密码不一致' })).toBeVisible({ timeout: 5000 });
  });

  test('6. 恢复原始资料', async () => {
    // 导航到个人资料页面
    await page.goto(getFullUrl(ROUTES.PROFILE));
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // 恢复原始数据
    const nameInput = page.locator('input[placeholder="请输入姓名"]').first();
    await nameInput.clear();
    await nameInput.fill('管理员');

    const emailInput = page.locator('input[placeholder="请输入邮箱（选填）"]').first();
    await emailInput.clear();

    const phoneInput = page.locator('input[placeholder="请输入手机号"]').first();
    await phoneInput.clear();

    // 点击保存按钮
    await page.locator('button:has-text("保存资料")').first().click();

    // 验证提示消息
    await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.el-message--success').first()).toContainText('成功');

    // 等待跳转到登录页
    await page.waitForTimeout(3000);

    // 验证已跳转到登录页
    await expect(page).toHaveURL(/.*login.*/);
  });
});
