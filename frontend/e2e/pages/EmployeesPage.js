/**
 * 员工管理页面对象
 */
import { BasePage } from './BasePage.js';

export class EmployeesPage extends BasePage {
  constructor(page) {
    super(page);
    
    // 页面标题
    this.pageTitle = page.getByRole('heading', { name: '员工管理' });
    
    // 搜索和筛选
    this.searchInput = page.getByPlaceholder('请输入姓名');
    this.statusSelect = page.locator('.el-select').first();
    this.searchButton = page.getByRole('button', { name: '搜索' });
    this.resetButton = page.getByRole('button', { name: '重置' });
    
    // 员工表格
    this.employeeTable = page.locator('.el-table');
    this.tableRows = page.locator('.el-table__row');
    
    // 操作按钮
    this.createButton = page.getByRole('button', { name: '新建员工' });
    this.editButton = page.locator('button:has-text("编辑")').first();
    this.deleteButton = page.locator('button:has-text("删除")').first();
    
    // 分页
    this.pagination = page.locator('.el-pagination');
  }

  async goto() {
    await super.goto('/employees');
  }

  async expectPageLoaded() {
    await this.waitForPageLoad();
    await this.pageTitle.waitFor({ state: 'visible', timeout: 5000 });
  }
}
