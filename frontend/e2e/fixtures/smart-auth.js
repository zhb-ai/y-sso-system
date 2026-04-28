/**
 * 智能认证管理器
 * 统一处理真实后端场景下的登录、鉴权校验和受保护路由导航。
 */
import {
  AUTH_STORAGE_FILE,
  E2E_REQUIRE_ADMIN,
  TEST_CREDENTIALS,
  ROUTES,
  TIMEOUTS,
  getFullUrl
} from './test-config.js';

const LOGIN_RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 3000,
  retryOnErrors: ['网络错误', 'NetworkError', 'Failed to fetch', 'net::']
};

function isPrimaryLoginRoute(url = '') {
  try {
    const pathname = new URL(url).pathname;
    return pathname === ROUTES.LOGIN;
  } catch {
    return url.includes('/login') && !url.includes(ROUTES.SSO_LOGIN);
  }
}

const SELECTORS = {
  loginForm: '.login-form',
  loginUsername: '.login-form input[placeholder="用户名"]',
  loginPassword: '.login-form input[placeholder="密码"]',
  loginSubmit: '.login-form button:has-text("登录")',
  appShell: '.el-menu, .page-header, .sidebar',
  ssoUserInfo: '.sso-username, .sso-user-info, .sso-user-detail',
  adminLink: 'a:has-text("管理后台")',
  changePasswordDialog: '.el-dialog'
};

function isRetryableError(error) {
  return LOGIN_RETRY_CONFIG.retryOnErrors.some(
    (errMsg) => error.message?.includes(errMsg) || error.stack?.includes(errMsg)
  );
}

function isNetworkOrTimeoutError(error) {
  return error.message?.includes('net::') ||
    error.message?.includes('Failed to fetch') ||
    error.message?.includes('NetworkError') ||
    error.message?.includes('timeout');
}

async function hasValidToken(page) {
  const storage = await page.evaluate(() => {
    try {
      return {
        token: localStorage.getItem('token') || sessionStorage.getItem('token'),
        userInfo: localStorage.getItem('userInfo')
      };
    } catch {
      return { token: null, userInfo: null };
    }
  });

  if (!storage.token) {
    return false;
  }

  try {
    const payload = JSON.parse(atob(storage.token.split('.')[1]));
    if (payload.exp && payload.exp * 1000 <= Date.now()) {
      return false;
    }
  } catch {
    // 某些环境 token 不一定是标准 JWT，只要存在即可继续由受保护路由兜底验证。
  }

  return !!storage.userInfo || !E2E_REQUIRE_ADMIN;
}

async function waitForLoginScreen(page) {
  await page.waitForURL((url) => isPrimaryLoginRoute(url.toString()), { timeout: TIMEOUTS.AUTH }).catch(() => {});
  await page.locator(SELECTORS.loginForm).waitFor({ timeout: TIMEOUTS.AUTH });
}

async function waitForPostLoginState(page) {
  await page.waitForFunction(
    ({ authSelector, ssoSelector, changePwdSelector }) => {
      const url = window.location.pathname;
      const appShell = document.querySelector(authSelector);
      const ssoUser = document.querySelector(ssoSelector);
      const changePwdDialog = Array.from(document.querySelectorAll(changePwdSelector)).some(
        (node) => node.textContent?.includes('首次登录') || node.textContent?.includes('修改密码')
      );
      const hasToken = !!localStorage.getItem('token') || !!sessionStorage.getItem('token');

      return Boolean(
        changePwdDialog ||
        (hasToken && (url === '/dashboard' || url === '/sso/login' || appShell || ssoUser))
      );
    },
    {
      authSelector: SELECTORS.appShell,
      ssoSelector: SELECTORS.ssoUserInfo,
      changePwdSelector: SELECTORS.changePasswordDialog
    },
    { timeout: TIMEOUTS.AUTH }
  );
}

export async function assertE2EAccountReady(page, { requireAdmin = E2E_REQUIRE_ADMIN } = {}) {
  const authState = await page.evaluate(() => {
    const rawUser = localStorage.getItem('userInfo');
    const user = rawUser ? JSON.parse(rawUser) : null;
    return {
      hasToken: !!localStorage.getItem('token') || !!sessionStorage.getItem('token'),
      user
    };
  });

  if (!authState.hasToken || !authState.user) {
    throw new Error('E2E 登录后未拿到完整认证状态（token 或 userInfo 缺失）');
  }

  if (authState.user.must_change_password) {
    throw new Error(`E2E 测试账号 ${TEST_CREDENTIALS.username} 需要先修改默认密码，当前环境不适合跑后台联调测试`);
  }

  if (requireAdmin && !Array.isArray(authState.user.roles || []) && authState.user.roles !== undefined) {
    throw new Error('E2E 登录用户角色数据格式异常，无法判断是否具备后台访问权限');
  }

  if (requireAdmin && !(authState.user.roles || []).includes('admin')) {
    throw new Error(`E2E 测试账号 ${TEST_CREDENTIALS.username} 不具备 admin 角色，无法访问管理后台`);
  }
}

export async function ensureAuthenticatedPortal(page, options = {}) {
  const { requireAdmin = E2E_REQUIRE_ADMIN } = options;
  let currentUrl = page.url();

  if (!currentUrl || currentUrl === 'about:blank') {
    await page.goto(getFullUrl(ROUTES.SSO_LOGIN));
    currentUrl = page.url();
  }

  if (currentUrl.includes('/sso/login')) {
    await page.locator(SELECTORS.ssoUserInfo).first().waitFor({ timeout: TIMEOUTS.AUTH });
    await assertE2EAccountReady(page, { requireAdmin });
    return;
  }

  if (currentUrl.includes('/dashboard')) {
    await page.locator(SELECTORS.appShell).first().waitFor({ timeout: TIMEOUTS.AUTH });
    await assertE2EAccountReady(page, { requireAdmin });
    return;
  }

  if (await hasValidToken(page)) {
    await page.goto(getFullUrl(ROUTES.SSO_LOGIN));
    await page.locator(SELECTORS.ssoUserInfo).first().waitFor({ timeout: TIMEOUTS.AUTH });
    await assertE2EAccountReady(page, { requireAdmin });
    return;
  }

  throw new Error(`登录后未进入预期页面，当前 URL: ${currentUrl}`);
}

export async function openAdminDashboard(page) {
  await ensureAuthenticatedPortal(page, { requireAdmin: true });

  if (page.url().includes('/dashboard')) {
    return;
  }

  const adminLink = page.locator(SELECTORS.adminLink);
  await adminLink.waitFor({ timeout: TIMEOUTS.AUTH });
  await adminLink.click();
  await page.waitForURL('**/dashboard', { timeout: TIMEOUTS.AUTH });
  await page.locator(SELECTORS.appShell).first().waitFor({ timeout: TIMEOUTS.AUTH });
}

/**
 * 检查当前页面是否已登录（通过检测token或页面特征）
 * @param {Page} page - Playwright page 对象
 * @returns {Promise<boolean>}
 */
export async function isAuthenticated(page) {
  try {
    if (await hasValidToken(page)) {
      return true;
    }

    const currentUrl = page.url();
    if (!isPrimaryLoginRoute(currentUrl)) {
      const hasAuthenticatedElement = await page.locator(SELECTORS.appShell).first().isVisible().catch(() => false);
      const hasPortalUserInfo = await page.locator(SELECTORS.ssoUserInfo).first().isVisible().catch(() => false);
      if (hasAuthenticatedElement || hasPortalUserInfo) {
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

      await page.goto(getFullUrl(ROUTES.LOGIN));

      if (await isAuthenticated(page)) {
        await ensureAuthenticatedPortal(page);
        console.log('用户已具备有效登录态，跳过登录表单');
        return;
      }

      await waitForLoginScreen(page);

      const usernameInput = page.locator(SELECTORS.loginUsername).first();
      await usernameInput.fill(TEST_CREDENTIALS.username);

      const passwordInput = page.locator(SELECTORS.loginPassword).first();
      await passwordInput.fill(TEST_CREDENTIALS.password);

      await page.locator(SELECTORS.loginSubmit).click();
      await waitForPostLoginState(page);

      const hasChangePasswordDialog = await page.locator(SELECTORS.changePasswordDialog)
        .filter({ hasText: /首次登录|修改密码/ })
        .first()
        .isVisible()
        .catch(() => false);
      if (hasChangePasswordDialog) {
        throw new Error(`E2E 测试账号 ${TEST_CREDENTIALS.username} 登录后触发强制改密，请先处理测试环境账号`);
      }

      await ensureAuthenticatedPortal(page);
      console.log('登录成功');
      return;

    } catch (error) {
      lastError = error;

      if (isRetryableError(error) || isNetworkOrTimeoutError(error)) {
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
  const { checkAuth = true } = options;

  console.log(`导航到: ${path}`);
  await page.goto(getFullUrl(path));

  if (checkAuth) {
    const currentUrl = page.url();

    if (isPrimaryLoginRoute(currentUrl)) {
      console.log('检测到未登录或token失效，执行登录...');
      await login(page, true);
      console.log(`重新导航到: ${path}`);
      await page.goto(getFullUrl(path));
    } else {
      const authenticated = await isAuthenticated(page);
      if (!authenticated) {
        console.log('页面访问正常但认证状态异常，尝试登录...');
        await login(page, true);
        await page.goto(getFullUrl(path));
      }
    }
  }
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

export { AUTH_STORAGE_FILE };
