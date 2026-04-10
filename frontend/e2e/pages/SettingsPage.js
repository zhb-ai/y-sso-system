/**
 * 系统设置页面对象
 */
import { BasePage } from './BasePage.js';

export class SettingsPage extends BasePage {
  constructor(page) {
    super(page);
    
    // 页面标题
    this.pageTitle = page.getByRole('heading', { name: '系统设置' });
    
    // 设置表单
    this.systemNameInput = page.locator('input').filter({ hasText: /系统名称/ }).or(page.getByLabel('系统名称'));
    this.systemDescInput = page.locator('input').filter({ hasText: /系统描述/ }).or(page.getByLabel('系统描述'));
    
    // 保存按钮
    this.saveButton = page.getByRole('button', { name: '保存' });
    this.resetButton = page.getByRole('button', { name: '重置' });
    
    // 设置卡片/区块
    this.settingsCard = page.locator('.el-card').first();
    this.settingsForm = page.locator('.el-form').first();
  }

  async goto() {
    await super.goto('/settings');
  }

  async expectPageLoaded() {
    await this.waitForPageLoad();
    await this.pageTitle.waitFor({ state: 'visible', timeout: 5000 });
  }
}
