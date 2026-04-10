/**
 * 全局设置 - 执行一次登录并保存状态
 * 所有测试共享同一个登录状态，避免并发登录冲突
 */
import { chromium } from '@playwright/test';
import { TEST_CREDENTIALS, ROUTES, getFullUrl } from './test-config.js';
import { login } from './smart-auth.js';

async function globalSetup() {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('[Global Setup] 执行全局登录...');

  try {
    // 执行登录
    await login(page);

    // 保存登录状态
    await context.storageState({ path: 'playwright/.auth/user.json' });
    console.log('[Global Setup] 登录状态已保存');
  } catch (error) {
    console.error('[Global Setup] 登录失败:', error.message);
    throw error;
  } finally {
    await browser.close();
  }
}

export default globalSetup;
