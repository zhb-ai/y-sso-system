/**
 * 认证相关的 fixtures
 */
import { test as base, expect } from '@playwright/test';
import { BASE_URL, TEST_CREDENTIALS, ROUTES, getFullUrl } from './test-config.js';

// 菜单名称到URL路径的映射
const menuPathMap = {
  '仪表盘': ROUTES.DASHBOARD,
  '应用管理': ROUTES.APPLICATIONS,
  '用户管理': ROUTES.USERS,
  '角色管理': ROUTES.ROLES,
  'SSO 角色': ROUTES.SSO_ROLES,
  '组织架构': ROUTES.ORGANIZATION,
  '员工管理': ROUTES.EMPLOYEES,
  '系统设置': ROUTES.SETTINGS,
  '缓存管理': ROUTES.CACHE,
  '个人资料': ROUTES.PROFILE
};

// 登录重试配置
const LOGIN_RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 3000,
  retryOnErrors: ['网络错误', 'NetworkError', 'Failed to fetch', 'net::']
};

/**
 * 执行登录操作（带重试机制）
 */
export async function login(page) {
  let lastError = null;

  for (let attempt = 1; attempt <= LOGIN_RETRY_CONFIG.maxRetries; attempt++) {
    try {
      // 1. 访问登录页
      await page.goto(getFullUrl(ROUTES.LOGIN));

      // 2. 等待页面加载
      await page.waitForLoadState('networkidle');

      // 3. 输入用户名
      const usernameInput = page.locator('.login-form input[placeholder="用户名"]').first();
      await usernameInput.waitFor({ timeout: 10000 });
      await usernameInput.fill(TEST_CREDENTIALS.username);

      // 4. 输入密码
      const passwordInput = page.locator('.login-form input[placeholder="密码"]').first();
      await passwordInput.fill(TEST_CREDENTIALS.password);

      // 5. 点击登录按钮
      await page.locator('.login-form button:has-text("登录")').click();

      // 6. 等待跳转到SSO登录页或仪表盘
      await page.waitForTimeout(3000);

      // 7. 检查当前URL
      const currentUrl = page.url();

      // 8. 如果跳转到sso/login，需要点击"进入管理后台"
      if (currentUrl.includes('/sso/login')) {
        await page.locator('a').filter({ hasText: '进入管理后台' }).waitFor({ timeout: 10000 });
        await page.locator('a').filter({ hasText: '进入管理后台' }).click();
        await page.waitForURL('**/dashboard', { timeout: 10000 });
      }

      // 9. 检查登录是否成功（如果还在登录页则失败）
      const finalUrl = page.url();
      if (finalUrl.includes('/login')) {
        throw new Error('登录失败，仍在登录页面');
      }

      // 10. 等待页面完全加载
      await page.waitForTimeout(2000);

      // 登录成功
      return;

    } catch (error) {
      lastError = error;
      const isRetryableError = LOGIN_RETRY_CONFIG.retryOnErrors.some(
        errMsg => error.message?.includes(errMsg) || error.stack?.includes(errMsg)
      );

      // 检查是否是网络错误
      const isNetworkError = error.message?.includes('net::') ||
                            error.message?.includes('Failed to fetch') ||
                            error.message?.includes('NetworkError') ||
                            error.message?.includes('timeout');

      if (isRetryableError || isNetworkError) {
        console.log(`登录尝试 ${attempt}/${LOGIN_RETRY_CONFIG.maxRetries} 失败: ${error.message}`);

        if (attempt < LOGIN_RETRY_CONFIG.maxRetries) {
          console.log(`等待 ${LOGIN_RETRY_CONFIG.retryDelay / 1000} 秒后重试...`);
          await page.waitForTimeout(LOGIN_RETRY_CONFIG.retryDelay);
        }
      } else {
        // 非网络错误，直接抛出
        throw error;
      }
    }
  }

  // 所有重试都失败
  throw new Error(`登录失败，已重试 ${LOGIN_RETRY_CONFIG.maxRetries} 次: ${lastError?.message}`);
}

/**
 * 导航到指定菜单
 */
export async function navigateToMenu(page, menuName) {
  if (menuName === '仪表盘') {
    return;
  }
  
  // 尝试点击菜单项
  try {
    const menuItem = page.locator('.el-menu-item, .el-sub-menu__title').filter({ hasText: menuName });
    await menuItem.waitFor({ timeout: 5000 });
    await menuItem.click();
    await page.waitForTimeout(2000);
  } catch (e) {
    // 如果菜单点击失败，使用直接URL导航
    const path = menuPathMap[menuName];
    if (path) {
      // 先保存当前页面的cookie和localStorage
      const cookies = await page.context().cookies();
      
      await page.goto(getFullUrl(path));
      await page.waitForTimeout(3000);

      // 检查是否被重定向到登录页，如果是则重新登录
      const currentUrl = page.url();
      if (currentUrl.includes('/login')) {
        // 重新登录
        await login(page);
        // 再次导航到目标页面
        await page.goto(getFullUrl(path));
        await page.waitForTimeout(2000);
      }
    } else {
      throw new Error(`无法导航到菜单: ${menuName}`);
    }
  }
}

/**
 * 登录并导航到指定页面
 */
export async function loginAndNavigate(page, menuName) {
  await login(page);
  await navigateToMenu(page, menuName);
}
