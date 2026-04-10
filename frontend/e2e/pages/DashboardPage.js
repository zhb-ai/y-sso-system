/**
 * 仪表盘页面对象
 * 封装仪表盘相关的操作和元素选择器
 */
export class DashboardPage {
  constructor(page) {
    this.page = page;
    
    // 页面标题
    this.pageTitle = page.getByRole('heading', { name: '仪表盘' });
    this.welcomeText = page.locator('h5');
    
    // 统计卡片
    this.statCards = page.locator('.stat-card');
    this.applicationCount = page.locator('.stat-card').first().locator('h3');
    this.userCount = page.locator('.stat-card').nth(1).locator('h3');
    this.employeeCount = page.locator('.stat-card').nth(2).locator('h3');
    this.departmentCount = page.locator('.stat-card').nth(3).locator('h3');
    
    // 搜索和筛选
    this.searchUsernameInput = page.getByPlaceholder('请输入用户名');
    this.searchIpInput = page.getByPlaceholder('请输入登录IP');
    this.statusSelect = page.locator('.el-select').first();
    this.searchButton = page.getByRole('button', { name: '搜索' });
    this.resetButton = page.getByRole('button', { name: '重置' });
    
    // 登录记录表格
    this.loginRecordTable = page.locator('.el-table');
    this.tableRows = page.locator('.el-table__row');
    
    // 分页
    this.pagination = page.locator('.el-pagination');
  }

  /**
   * 验证页面加载成功
   */
  async expectPageLoaded() {
    await this.pageTitle.waitFor({ state: 'visible' });
    await this.welcomeText.waitFor({ state: 'visible' });
  }

  /**
   * 获取欢迎文本
   */
  async getWelcomeText() {
    return await this.welcomeText.textContent();
  }

  /**
   * 验证统计卡片显示
   */
  async expectStatCardsVisible() {
    await this.statCards.first().waitFor({ state: 'visible' });
    const count = await this.statCards.count();
    return count === 4;
  }

  /**
   * 搜索登录记录
   * @param {string} username - 用户名
   * @param {string} ip - IP地址
   * @param {string} status - 状态
   */
  async searchLoginRecords(username = '', ip = '', status = '') {
    if (username) {
      await this.searchUsernameInput.fill(username);
    }
    if (ip) {
      await this.searchIpInput.fill(ip);
    }
    if (status) {
      await this.statusSelect.click();
      await this.page.getByText(status).click();
    }
    await this.searchButton.click();
  }

  /**
   * 获取表格行数
   */
  async getTableRowCount() {
    return await this.tableRows.count();
  }

  /**
   * 点击重置按钮
   */
  async clickReset() {
    await this.resetButton.click();
  }
}
