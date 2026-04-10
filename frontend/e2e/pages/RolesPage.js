/**
 * 角色管理页面对象
 */
import { BasePage } from './BasePage.js';

export class RolesPage extends BasePage {
  constructor(page) {
    super(page);
    
    // 页面标题和操作按钮
    this.pageTitle = page.getByRole('heading', { name: '角色管理' });
    this.createButton = page.getByRole('button', { name: '新建角色' });
    
    // 角色表格
    this.roleTable = page.locator('.el-table');
    this.tableRows = page.locator('.el-table__row');
    
    // 操作按钮
    this.editButton = page.locator('button:has-text("编辑")').first();
    this.permissionsButton = page.locator('button:has-text("权限")').first();
    this.viewUsersButton = page.locator('button:has-text("查看用户")').first();
    this.deleteButton = page.locator('button:has-text("删除")').first();
    
    // 分页
    this.pagination = page.locator('.el-pagination');
  }

  async goto() {
    await super.goto('/roles');
  }

  async expectPageLoaded() {
    await this.waitForPageLoad();
    await this.pageTitle.waitFor({ state: 'visible', timeout: 5000 });
  }
}
