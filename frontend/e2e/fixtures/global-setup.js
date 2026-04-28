/**
 * 全局设置 - 执行一次登录并保存状态
 * 所有测试共享同一个登录状态，避免并发登录冲突
 */
import { chromium } from '@playwright/test';
import { AUTH_STORAGE_FILE } from './test-config.js';
import { login } from './smart-auth.js';

async function globalSetup() {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('[Global Setup] 执行全局登录...');

  try {
    await login(page);

    await context.storageState({ path: AUTH_STORAGE_FILE });
    console.log('[Global Setup] 登录状态已保存');
  } catch (error) {
    console.error('[Global Setup] 登录失败:', error.message);
    throw error;
  } finally {
    await browser.close();
  }
}

export default globalSetup;
