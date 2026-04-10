/**
 * 测试基础 fixtures
 * 提供登录和页面导航的共享功能
 */
import { test as base, expect } from '@playwright/test';
import { login, navigateToMenu } from './auth.js';
import { ROUTES, getFullUrl } from './test-config.js';

/**
 * 扩展的 test 对象，包含认证相关的 fixtures
 */
export const test = base.extend({
  /**
   * 已登录的页面
   * 每个 test.describe.serial 块中只登录一次
   */
  authenticatedPage: async ({ page }, use) => {
    await login(page);
    await use(page);
  },
});

export { expect };

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

/**
 * 导航到指定菜单（已登录状态下）
 * @param {Page} page - Playwright page 对象
 * @param {string} menuName - 菜单名称
 */
export async function navigateToPage(page, menuName) {
  const menuPathMap = getMenuPathMap();

  if (menuName === '仪表盘') {
    await page.goto(getFullUrl(ROUTES.DASHBOARD));
    await page.waitForTimeout(2000);
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
      await page.goto(getFullUrl(path));
      await page.waitForTimeout(3000);
    } else {
      throw new Error(`无法导航到菜单: ${menuName}`);
    }
  }
}
