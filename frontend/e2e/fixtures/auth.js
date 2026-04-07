/**
 * 认证相关的 fixtures
 */
import { test as base, expect } from '@playwright/test';

// 菜单名称到URL路径的映射
const menuPathMap = {
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

/**
 * 执行登录操作
 */
export async function login(page) {
  // 1. 访问登录页
  await page.goto('http://localhost:5200/login');
  
  // 2. 等待页面加载
  await page.waitForLoadState('networkidle');
  
  // 3. 输入用户名
  const usernameInput = page.locator('.login-form input[placeholder="用户名"]').first();
  await usernameInput.waitFor({ timeout: 10000 });
  await usernameInput.fill('admin');
  
  // 4. 输入密码
  const passwordInput = page.locator('.login-form input[placeholder="密码"]').first();
  await passwordInput.fill('admin123');
  
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
  
  // 9. 等待页面完全加载
  await page.waitForTimeout(2000);
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
      
      await page.goto(`http://localhost:5200${path}`);
      await page.waitForTimeout(3000);
      
      // 检查是否被重定向到登录页，如果是则重新登录
      const currentUrl = page.url();
      if (currentUrl.includes('/login')) {
        // 重新登录
        await login(page);
        // 再次导航到目标页面
        await page.goto(`http://localhost:5200${path}`);
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
