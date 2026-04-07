/**
 * 用户管理页面对象
 * 封装用户管理相关的操作和元素选择器
 */
export class UsersPage {
  constructor(page) {
    this.page = page;

    // 页面标题和操作按钮
    this.pageTitle = page.getByRole('heading', { name: '用户管理' });
    this.createButton = page.getByRole('button', { name: '新建用户' });

    // 搜索和筛选
    this.searchInput = page.getByPlaceholder('请输入用户名、姓名或邮箱');
    this.statusSelect = page.locator('.el-select').first();
    this.roleSelect = page.locator('.el-select').nth(1);
    this.searchButton = page.getByRole('button', { name: '搜索' });
    this.resetButton = page.getByRole('button', { name: '重置' });

    // 用户表格
    this.userTable = page.locator('.el-table');
    this.tableRows = page.locator('.el-table__row');

    // 分页
    this.pagination = page.locator('.el-pagination');

    // 创建用户对话框
    this.createDialog = page.locator('.el-dialog');
    this.usernameInput = page.locator('.el-dialog input').first();
    this.nameInput = page.locator('.el-dialog input').nth(1);
    this.emailInput = page.locator('.el-dialog input[type="email"]');
    this.phoneInput = page.locator('.el-dialog input').nth(3);
    this.passwordInput = page.locator('.el-dialog input[type="password"]');
    this.confirmButton = page.getByRole('button', { name: '确定' });
    this.cancelButton = page.getByRole('button', { name: '取消' });
  }

  /**
   * 导航到用户管理页面
   */
  async goto() {
    await this.page.goto('/users');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 验证页面加载成功
   */
  async expectPageLoaded() {
    await this.pageTitle.waitFor({ state: 'visible' });
    await this.createButton.waitFor({ state: 'visible' });
  }

  /**
   * 搜索用户
   * @param {string} keyword - 搜索关键词
   */
  async searchUsers(keyword) {
    await this.searchInput.fill(keyword);
    await this.searchButton.click();
    await this.page.waitForTimeout(500);
  }

  /**
   * 按状态筛选
   * @param {string} status - 状态值
   */
  async filterByStatus(status) {
    await this.statusSelect.click();
    await this.page.getByText(status).click();
    await this.searchButton.click();
    await this.page.waitForTimeout(500);
  }

  /**
   * 点击新建用户按钮
   */
  async clickCreateUser() {
    await this.createButton.click();
    await this.createDialog.waitFor({ state: 'visible' });
  }

  /**
   * 填写创建用户表单
   * @param {Object} userData - 用户数据
   */
  async fillCreateForm(userData) {
    if (userData.username) {
      await this.usernameInput.fill(userData.username);
    }
    if (userData.name) {
      await this.nameInput.fill(userData.name);
    }
    if (userData.email) {
      await this.emailInput.fill(userData.email);
    }
    if (userData.phone) {
      await this.phoneInput.fill(userData.phone);
    }
    if (userData.password) {
      await this.passwordInput.fill(userData.password);
    }
  }

  /**
   * 提交创建用户表单
   */
  async submitCreateForm() {
    await this.confirmButton.click();
  }

  /**
   * 取消创建用户
   */
  async cancelCreate() {
    await this.cancelButton.click();
  }

  /**
   * 获取表格行数
   */
  async getTableRowCount() {
    return await this.tableRows.count();
  }

  /**
   * 点击表格中的编辑按钮
   * @param {number} rowIndex - 行索引
   */
  async clickEditUser(rowIndex = 0) {
    const row = this.tableRows.nth(rowIndex);
    await row.locator('button:has-text("编辑")').click();
  }

  /**
   * 点击表格中的删除按钮
   * @param {number} rowIndex - 行索引
   */
  async clickDeleteUser(rowIndex = 0) {
    const row = this.tableRows.nth(rowIndex);
    await row.locator('button:has-text("删除")').click();
  }

  /**
   * 点击表格中的分配角色按钮
   * @param {number} rowIndex - 行索引
   */
  async clickAssignRole(rowIndex = 0) {
    const row = this.tableRows.nth(rowIndex);
    await row.locator('button:has-text("分配角色")').click();
  }

  /**
   * 点击重置按钮
   */
  async clickReset() {
    await this.resetButton.click();
    await this.page.waitForTimeout(300);
  }
}
