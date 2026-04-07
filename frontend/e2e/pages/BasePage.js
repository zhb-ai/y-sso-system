/**
 * 基础页面对象
 * 所有页面的基类，包含通用方法
 */
export class BasePage {
  constructor(page) {
    this.page = page;
    this.pageTitle = page.locator('.page-header h2, h2');
    this.loadingIndicator = page.locator('.el-loading-mask');
  }

  /**
   * 导航到指定页面
   */
  async goto(path) {
    await this.page.goto(path);
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 等待页面加载完成
   */
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
    // 等待加载动画消失
    await this.loadingIndicator.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
  }

  /**
   * 验证页面标题存在
   */
  async expectPageTitleVisible() {
    await this.pageTitle.waitFor({ state: 'visible', timeout: 5000 });
  }

  /**
   * 获取页面标题文本
   */
  async getPageTitle() {
    return await this.pageTitle.textContent();
  }

  /**
   * 验证页面 URL
   */
  async expectUrl(path) {
    await this.page.waitForURL(path, { timeout: 10000 });
  }
}
