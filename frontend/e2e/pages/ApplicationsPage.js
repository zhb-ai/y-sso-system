/**
 * 应用管理页面对象
 */
import { BasePage } from './BasePage.js';

export class ApplicationsPage extends BasePage {
  constructor(page) {
    super(page);
    
    // 页面标题和操作按钮
    this.pageTitle = page.getByRole('heading', { name: '应用管理' });
    this.createButton = page.getByRole('button', { name: '新建应用' });
    
    // 搜索和筛选
    this.searchInput = page.getByPlaceholder('请输入应用名称');
    this.statusSelect = page.locator('.el-select').first();
    this.searchButton = page.getByRole('button', { name: '搜索' });
    this.resetButton = page.getByRole('button', { name: '重置' });
    
    // 应用表格
    this.appTable = page.locator('.el-table');
    this.tableRows = page.locator('.el-table__row');
    
    // 分页
    this.pagination = page.locator('.el-pagination');
    
    // 空状态
    this.emptyState = page.locator('.el-empty');
  }

  async goto() {
    await super.goto('/applications');
  }

  async expectPageLoaded() {
    await this.waitForPageLoad();
    await this.pageTitle.waitFor({ state: 'visible', timeout: 5000 });
  }
}
