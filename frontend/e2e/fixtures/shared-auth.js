/**
 * 共享认证工具
 * 用于已登录状态的测试，直接使用全局登录状态
 */
import { ROUTES } from './test-config.js';
import { getMenuPathMap as getSharedMenuPathMap, smartNavigate, openAdminDashboard } from './smart-auth.js';

/**
 * 导航到指定页面（假设已登录）
 * @param {Page} page - Playwright page 对象
 * @param {string} path - 目标路径
 * @param {Object} options - 配置选项
 */
export async function navigateTo(page, path, options = {}) {
  console.log(`[导航] 访问页面: ${path}`);
  await openAdminDashboard(page);
  await smartNavigate(page, path, options);
}

/**
 * 导航到指定菜单页面
 * @param {Page} page - Playwright page 对象
 * @param {string} menuName - 菜单名称
 * @param {Object} options - 配置选项
 */
export async function navigateToMenu(page, menuName, options = {}) {
  const path = getSharedMenuPathMap()[menuName];
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
  return getSharedMenuPathMap();
}

export { ROUTES } from './test-config.js';
