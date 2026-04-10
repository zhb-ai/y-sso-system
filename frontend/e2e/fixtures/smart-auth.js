/**
 * 智能认证管理器
 * 支持token检测和自动登录，避免重复登录
 */
import { TEST_CREDENTIALS, ROUTES, getFullUrl } from './test-config.js';

// 登录重试配置
const LOGIN_RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 3000,
  retryOnErrors: ['网络错误', 'NetworkError', 'Failed to fetch', 'net::']
};

// 存储认证状态的文件路径（用于worker间共享）
const AUTH_STORAGE_FILE = 'playwright/.auth/user.json';

/**
 * 检查当前页面是否已登录（通过检测token或页面特征）
 * @param {Page} page - Playwright page 对象
 * @returns {Promise<boolean>}
 */
export async function isAuthenticated(page) {
  try {
    // 方法1: 检查localStorage中的token
    const token = await page.evaluate(() => {
      return localStorage.getItem('token') || sessionStorage.getItem('token');
    });

    if (token) {
      // 验证token是否有效（检查是否过期）
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.exp && payload.exp * 1000 > Date.now()) {
          return true;
        }
      } catch (e) {
        // token格式不正确，继续检查其他方式
      }
    }

    // 方法2: 检查当前URL是否不是登录页
    const currentUrl = page.url();
    if (!currentUrl.includes('/login') && !currentUrl.includes('/sso/login')) {
      // 方法3: 检查页面是否存在登录后的特征元素
      const hasAuthenticatedElement = await page.locator('.el-menu, .page-header, .sidebar').first().isVisible().catch(() => false);
      if (hasAuthenticatedElement) {
        return true;
      }
    }

    return false;
  } catch (error) {
    return false;
  }
}

/**
 * 执行登录操作（带重试机制）
 * @param {Page} page - Playwright page 对象
 * @param {boolean} force - 是否强制重新登录
 */
export async function login(page, force = false) {
  // 如果不是强制登录，先检查是否已认证
  if (!force) {
    const authenticated = await isAuthenticated(page);
    if (authenticated) {
      console.log('用户已登录，跳过登录步骤');
      return;
    }
  }

  let lastError = null;

  for (let attempt = 1; attempt <= LOGIN_RETRY_CONFIG.maxRetries; attempt++) {
    try {
      console.log(`执行登录... (尝试 ${attempt}/${LOGIN_RETRY_CONFIG.maxRetries})`);

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

      console.log('登录成功');
      return;

    } catch (error) {
      lastError = error;
      const isRetryableError = LOGIN_RETRY_CONFIG.retryOnErrors.some(
        errMsg => error.message?.includes(errMsg) || error.stack?.includes(errMsg)
      );

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
        throw error;
      }
    }
  }

  throw new Error(`登录失败，已重试 ${LOGIN_RETRY_CONFIG.maxRetries} 次: ${lastError?.message}`);
}

/**
 * 智能导航到指定页面
 * 如果未登录会自动登录，如果token失效会重新登录
 * @param {Page} page - Playwright page 对象
 * @param {string} path - 目标路径
 * @param {Object} options - 配置选项
 */
export async function smartNavigate(page, path, options = {}) {
  const { checkAuth = true, timeout = 10000 } = options;

  // 1. 直接访问目标页面
  console.log(`导航到: ${path}`);
  await page.goto(getFullUrl(path));
  await page.waitForLoadState('networkidle');

  // 2. 如果需要检查认证状态
  if (checkAuth) {
    // 等待一下让页面完成认证检查
    await page.waitForTimeout(1000);

    // 检查是否被重定向到登录页
    const currentUrl = page.url();

    if (currentUrl.includes('/login')) {
      console.log('检测到未登录或token失效，执行登录...');
      // 执行登录
      await login(page, true);

      // 重新导航到目标页面
      console.log(`重新导航到: ${path}`);
      await page.goto(getFullUrl(path));
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
    } else {
      // 检查是否已认证
      const authenticated = await isAuthenticated(page);
      if (!authenticated) {
        console.log('页面访问正常但认证状态异常，尝试登录...');
        await login(page, true);
        await page.goto(getFullUrl(path));
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
      }
    }
  }

  // 3. 等待页面稳定
  await page.waitForTimeout(1000);
}

/**
 * 菜单名称到URL路径的映射
 */
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

/**
 * 智能导航到指定菜单页面
 * @param {Page} page - Playwright page 对象
 * @param {string} menuName - 菜单名称
 * @param {Object} options - 配置选项
 */
export async function smartNavigateToMenu(page, menuName, options = {}) {
  const path = menuPathMap[menuName];
  if (!path) {
    throw new Error(`未知的菜单名称: ${menuName}`);
  }

  await smartNavigate(page, path, options);
}

/**
 * 获取菜单路径映射
 * @returns {Object}
 */
export function getMenuPathMap() {
  return { ...menuPathMap };
}
