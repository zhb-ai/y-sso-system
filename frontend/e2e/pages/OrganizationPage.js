/**
 * 组织架构页面对象
 */
import { BasePage } from './BasePage.js';

export class OrganizationPage extends BasePage {
  constructor(page) {
    super(page);
    
    // 页面标题
    this.pageTitle = page.getByRole('heading', { name: '组织架构' });
    
    // 操作按钮
    this.createEmployeeButton = page.getByRole('button', { name: '新建员工' });
    this.createOrgButton = page.getByRole('button', { name: '新建组织' });
    this.editOrgButton = page.getByRole('button', { name: '编辑组织' });
    this.syncWechatButton = page.getByRole('button', { name: '同步企业微信' });
    
    // 部门树
    this.deptTree = page.locator('.el-tree');
    this.deptNodes = page.locator('.el-tree-node');
    
    // 员工表格
    this.employeeTable = page.locator('.el-table');
    this.tableRows = page.locator('.el-table__row');
    
    // 分页
    this.pagination = page.locator('.el-pagination');
  }

  async goto() {
    await super.goto('/organization');
  }

  async expectPageLoaded() {
    await this.waitForPageLoad();
    await this.pageTitle.waitFor({ state: 'visible', timeout: 5000 });
  }
}
