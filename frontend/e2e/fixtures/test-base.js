/**
 * 测试基础 fixtures
 * 提供登录和页面导航的共享功能
 */
import { test as base, expect } from '@playwright/test';
import { login, navigateToMenu } from './auth.js';

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
    '仪表盘': '/dashboard',
    '应用管理': '/applications',
    '用户管理': '/users',
    '角色管理': '/roles',
    'SSO 角色': '/sso-roles',
    '组织架构': '/organization',
    '员工管理': '/employees',
    '系统设置': '/settings',
    '缓存管理': '/cache'
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
    await page.goto('http://localhost:5200/dashboard');
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
      await page.goto(`http://localhost:5200${path}`);
      await page.waitForTimeout(3000);
    } else {
      throw new Error(`无法导航到菜单: ${menuName}`);
    }
  }
}
