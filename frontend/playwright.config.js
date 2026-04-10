// @ts-check
import { defineConfig, devices } from '@playwright/test';

/**
 * Y-SSO System E2E 测试配置
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e',

  /* 全局设置 - 执行一次登录 */
  globalSetup: './e2e/fixtures/global-setup.js',

  /* 启用完全并行运行测试 - 每个测试文件独立运行 */
  fullyParallel: true,

  /* 在 CI 中禁止 test.only */
  forbidOnly: !!process.env.CI,

  /* 重试次数 */
  retries: process.env.CI ? 2 : 0,

  /* 工作进程数 - 根据 CPU 核心数自动调整，最多4个 */
  workers: process.env.CI ? 2 : 4,
  
  /* 报告器配置 */
  reporter: [
    ['html', { open: 'never' }],
    ['list']
  ],
  
  /* 共享配置 */
  use: {
    /* 基础 URL */
    baseURL: 'http://localhost:5200',

    /* 使用全局登录状态 */
    storageState: 'playwright/.auth/user.json',

    /* 收集追踪信息 */
    trace: 'on-first-retry',

    /* 失败时截图 */
    screenshot: 'only-on-failure',

    /* 失败时录制视频 */
    video: 'on-first-retry',

    /* 视口大小 */
    viewport: { width: 1280, height: 720 },

    /* 动作超时 */
    actionTimeout: 15000,

    /* 导航超时 */
    navigationTimeout: 30000,
  },

  /* 项目配置 */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  /* 本地开发服务器配置 */
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5200',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
