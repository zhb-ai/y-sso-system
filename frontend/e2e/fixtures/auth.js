/**
 * 认证相关的 fixtures
 */
import { test as base, expect } from '@playwright/test';
import { ROUTES, getFullUrl } from './test-config.js';
import {
  getMenuPathMap,
  login as smartLogin,
  openAdminDashboard,
  smartNavigate
} from './smart-auth.js';

export async function login(page, force = false) {
  await smartLogin(page, force);
}

/**
 * 导航到指定菜单
 */
export async function navigateToMenu(page, menuName) {
  if (menuName === '仪表盘') {
    return;
  }

  const path = getMenuPathMap()[menuName];
  if (!path) {
    throw new Error(`无法导航到菜单: ${menuName}`);
  }

  await smartNavigate(page, path, { checkAuth: true });
}

/**
 * 登录并导航到指定页面
 */
export async function loginAndNavigate(page, menuName) {
  await smartLogin(page);
  await openAdminDashboard(page);
  if (menuName !== '仪表盘') {
    await navigateToMenu(page, menuName);
  }
}
