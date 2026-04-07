/**
 * SSO角色管理页面对象
 */
import { BasePage } from './BasePage.js';

export class SSORolesPage extends BasePage {
  constructor(page) {
    super(page);
    
    // 页面标题和操作按钮
    this.pageTitle = page.getByRole('heading', { name: /SSO.*角色/ });
    this.createButton = page.getByRole('button', { name: '新建角色' });
    
    // 搜索和筛选
    this.searchInput = page.getByPlaceholder('请输入角色名称');
    this.searchButton = page.getByRole('button', { name: '搜索' });
    this.resetButton = page.getByRole('button', { name: '重置' });
    
    // 角色表格
    this.roleTable = page.locator('.el-table');
    this.tableRows = page.locator('.el-table__row');
    
    // 操作按钮
    this.editButton = page.locator('button:has-text("编辑")').first();
    this.deleteButton = page.locator('button:has-text("删除")').first();
    
    // 分页
    this.pagination = page.locator('.el-pagination');
  }

  async goto() {
    await super.goto('/sso-roles');
  }

  async expectPageLoaded() {
    await this.waitForPageLoad();
    await this.pageTitle.waitFor({ state: 'visible', timeout: 5000 });
  }
}
