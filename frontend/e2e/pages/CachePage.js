/**
 * 缓存管理页面对象
 */
import { BasePage } from './BasePage.js';

export class CachePage extends BasePage {
  constructor(page) {
    super(page);
    
    // 页面标题
    this.pageTitle = page.getByRole('heading', { name: '缓存管理' });
    
    // 操作按钮
    this.refreshButton = page.getByRole('button', { name: '刷新' });
    this.clearAllButton = page.getByRole('button', { name: '清空全部' });
    
    // 缓存统计
    this.cacheStats = page.locator('.cache-stats, .stats-cards');
    
    // 缓存列表表格
    this.cacheTable = page.locator('.el-table');
    this.tableRows = page.locator('.el-table__row');
    
    // 查看按钮
    this.viewButton = page.locator('button:has-text("查看")').first();
    this.clearButton = page.locator('button:has-text("清空")').first();
  }

  async goto() {
    await super.goto('/cache');
  }

  async expectPageLoaded() {
    await this.waitForPageLoad();
    await this.pageTitle.waitFor({ state: 'visible', timeout: 5000 });
  }
}
