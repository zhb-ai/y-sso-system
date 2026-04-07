/**
 * 登录页面对象
 * 封装登录相关的操作和元素选择器
 * 默认测试账号: admin / admin123
 */
export class LoginPage {
  constructor(page) {
    this.page = page;
    
    // 元素选择器 - 使用更可靠的选择器
    // 用户名输入框 - 使用 placeholder
    this.usernameInput = page.locator('input[placeholder="用户名"]');
    // 密码输入框 - 使用 placeholder
    this.passwordInput = page.locator('input[placeholder="密码"]');
    // 登录按钮 - 使用文本内容
    this.loginButton = page.getByRole('button', { name: '登录' });
    // 记住密码复选框
    this.rememberCheckbox = page.getByText('记住密码');
    // 忘记密码链接
    this.forgotPasswordLink = page.getByText('忘记密码？');
    // 企业微信登录按钮
    this.wechatLoginButton = page.getByText('企业微信登录');
    
    // 错误提示
    this.errorMessage = page.locator('.el-message--error, .el-form-item__error');
    
    // 登录表单
    this.loginForm = page.locator('.login-form');
  }

  /**
   * 导航到登录页面
   */
  async goto() {
    await this.page.goto('/login');
    // 等待页面加载完成
    await this.page.waitForLoadState('networkidle');
    // 确保登录表单可见
    await this.loginForm.waitFor({ state: 'visible', timeout: 10000 });
  }

  /**
   * 验证页面加载完成
   */
  async expectPageLoaded() {
    await this.loginForm.waitFor({ state: 'visible', timeout: 10000 });
    await this.usernameInput.waitFor({ state: 'visible', timeout: 5000 });
    await this.passwordInput.waitFor({ state: 'visible', timeout: 5000 });
    await this.loginButton.waitFor({ state: 'visible', timeout: 5000 });
  }

  /**
   * 执行登录操作
   * @param {string} username - 用户名，默认为 'admin'
   * @param {string} password - 密码，默认为 'admin123'
   * @param {boolean} remember - 是否记住密码
   */
  async login(username = 'admin', password = 'admin123', remember = false) {
    // 等待输入框可用
    await this.usernameInput.waitFor({ state: 'visible', timeout: 5000 });
    await this.passwordInput.waitFor({ state: 'visible', timeout: 5000 });
    
    // 清空并填写用户名
    await this.usernameInput.fill(username);
    
    // 清空并填写密码
    await this.passwordInput.fill(password);
    
    // 记住密码选项
    if (remember) {
      await this.rememberCheckbox.click();
    }
    
    // 点击登录按钮
    await this.loginButton.click();
  }

  /**
   * 验证登录成功
   * 等待跳转到仪表盘页面
   */
  async expectLoginSuccess() {
    // 等待 URL 变化
    await this.page.waitForURL('/dashboard', { timeout: 10000 });
    // 等待页面加载完成
    await this.page.waitForLoadState('networkidle');
    // 验证仪表盘元素存在
    await this.page.locator('h2:has-text("仪表盘")').waitFor({ state: 'visible', timeout: 5000 });
  }

  /**
   * 验证登录失败
   * @param {string} expectedMessage - 预期的错误消息（可选）
   */
  async expectLoginFailure(expectedMessage) {
    // 等待错误消息出现
    await this.errorMessage.waitFor({ state: 'visible', timeout: 5000 });
    
    // 如果提供了预期消息，验证消息内容
    if (expectedMessage) {
      await this.errorMessage.getByText(expectedMessage).waitFor({ timeout: 3000 });
    }
  }

  /**
   * 验证仍在登录页面
   */
  async expectStillOnLoginPage() {
    await this.page.waitForURL('/login');
    await this.loginForm.waitFor({ state: 'visible' });
  }

  /**
   * 点击忘记密码
   */
  async clickForgotPassword() {
    await this.forgotPasswordLink.click();
  }

  /**
   * 点击企业微信登录
   */
  async clickWechatLogin() {
    await this.wechatLoginButton.click();
  }

  /**
   * 快速登录 - 使用默认测试账号
   */
  async quickLogin() {
    await this.login('admin', 'admin123');
    await this.expectLoginSuccess();
  }
}
