/**
 * 智能测试基础 fixtures
 * 优化：直接访问测试页面，如果token不存在或失效则自动从登录页开始
 */
import { test as base, expect } from '@playwright/test';
import {
  AUTH_STORAGE_FILE,
  login,
  isAuthenticated,
  smartNavigate,
  smartNavigateToMenu,
  getMenuPathMap,
  openAdminDashboard
} from './smart-auth.js';
import { ROUTES, getFullUrl } from './test-config.js';

/**
 * 扩展的 test 对象，包含智能认证相关的 fixtures
 */
export const test = base.extend({
  /**
   * 已智能认证的页面
   * 会自动检测登录状态，如果未登录则执行登录
   */
  authenticatedPage: async ({ page }, use) => {
    const auth = await isAuthenticated(page);
    if (!auth) {
      await login(page);
    }
    await use(page);
  },

  /**
   * 带存储状态的上下文（用于跨测试保持登录状态）
   */
  authenticatedContext: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: AUTH_STORAGE_FILE
    });
    const page = await context.newPage();
    await openAdminDashboard(page);

    await use({ context, page });
    await context.close();
  }
});

export { expect };

/**
 * 创建智能页面测试套件
 * 自动处理登录状态，直接访问目标页面
 * @param {string} pageName - 页面名称（用于日志）
 * @param {string} route - 路由路径
 * @param {Function} testCallback - 测试回调函数
 */
export function createSmartPageTests(pageName, route, testCallback) {
  return test.describe.serial(`${pageName}页面测试`, () => {
    let page;
    let context;
    let isAuthReady = false;

    test.beforeAll(async ({ browser }) => {
      // 创建新的浏览器上下文
      context = await browser.newContext({ storageState: AUTH_STORAGE_FILE });
      page = await context.newPage();

      console.log(`[${pageName}] 开始测试，直接访问页面: ${route}`);
      await smartNavigate(page, route, { checkAuth: true });
      isAuthReady = true;
      console.log(`[${pageName}] 页面准备完成`);
    });

    test.afterAll(async () => {
      if (context) {
        await context.close();
      }
    });

    // 执行具体的测试
    testCallback(page, () => isAuthReady);
  });
}

/**
 * 智能导航到指定页面
 * @param {Page} page - Playwright page 对象
 * @param {string} path - 目标路径
 * @param {Object} options - 配置选项
 */
export async function navigateTo(page, path, options = {}) {
  return await smartNavigate(page, path, options);
}

/**
 * 智能导航到指定菜单页面
 * @param {Page} page - Playwright page 对象
 * @param {string} menuName - 菜单名称
 * @param {Object} options - 配置选项
 */
export async function navigateToMenu(page, menuName, options = {}) {
  return await smartNavigateToMenu(page, menuName, options);
}

/**
 * 重新导出智能认证函数
 */
export {
  AUTH_STORAGE_FILE,
  login,
  isAuthenticated,
  openAdminDashboard,
  smartNavigate,
  smartNavigateToMenu,
  getMenuPathMap
};

/**
 * 重新导出配置
 */
export { ROUTES, getFullUrl } from './test-config.js';
