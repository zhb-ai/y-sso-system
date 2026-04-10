/**
 * 单点登录页面对象
 */
import { BasePage } from './BasePage.js';

export class SSOLoginPage extends BasePage {
  constructor(page) {
    super(page);
    
    // 页面标题
    this.headerTitle = page.locator('.login-header h1');
    this.headerDesc = page.locator('.login-header p');
    
    // 登录表单
    this.usernameInput = page.locator('input[placeholder="请输入用户名"]').or(page.getByPlaceholder('用户名'));
    this.passwordInput = page.locator('input[placeholder="请输入密码"]').or(page.getByPlaceholder('密码'));
    this.loginButton = page.locator('button:has-text("登录并授权")').or(page.getByRole('button', { name: '登录' }));
    
    // 企业微信登录
    this.wechatLoginButton = page.locator('button:has-text("企业微信")');
    
    // 授权相关
    this.authorizeSection = page.locator('.sso-authorize-section');
    this.userInfo = page.locator('.sso-user-info');
    this.scopeInfo = page.locator('.sso-scope-info');
    this.authorizeButton = page.locator('button:has-text("授权并继续")');
    this.cancelButton = page.locator('button:has-text("取消")');
    
    // 应用列表
    this.appList = page.locator('.sso-app-list');
    this.appCard = page.locator('.sso-app-card');
    
    // 页脚链接
    this.adminLink = page.locator('a:has-text("管理后台")');
    this.logoutLink = page.locator('a:has-text("退出登录")');
  }

  async goto() {
    await super.goto('/sso/login');
  }

  async expectPageLoaded() {
    await this.waitForPageLoad();
    await this.headerTitle.waitFor({ state: 'visible', timeout: 5000 });
  }
}
