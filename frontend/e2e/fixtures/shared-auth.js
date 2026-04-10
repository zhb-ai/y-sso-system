/**
 * 共享认证工具
 * 用于已登录状态的测试，直接使用全局登录状态
 */
import { ROUTES, getFullUrl } from './test-config.js';

/**
 * 导航到指定页面（假设已登录）
 * @param {Page} page - Playwright page 对象
 * @param {string} path - 目标路径
 * @param {Object} options - 配置选项
 */
export async function navigateTo(page, path, options = {}) {
  const { timeout = 10000, waitForLoad = true } = options;

  console.log(`[导航] 访问页面: ${path}`);
  await page.goto(getFullUrl(path));

  if (waitForLoad) {
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  }

  // 检查是否被重定向到登录页（全局状态可能过期）
  const currentUrl = page.url();
  if (currentUrl.includes('/login')) {
    throw new Error('登录状态已过期，请重新运行测试');
  }
}

/**
 * 导航到指定菜单页面
 * @param {Page} page - Playwright page 对象
 * @param {string} menuName - 菜单名称
 * @param {Object} options - 配置选项
 */
export async function navigateToMenu(page, menuName, options = {}) {
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

  const path = menuPathMap[menuName];
  if (!path) {
    throw new Error(`未知的菜单名称: ${menuName}`);
  }

  await navigateTo(page, path, options);
}

/**
 * 获取菜单路径映射
 * @returns {Object}
 */
export function getMenuPathMap() {
  return {
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
}

export { ROUTES, getFullUrl } from './test-config.js';
