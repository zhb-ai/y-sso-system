---
name: "webapp-testing"
description: "Set up and run end-to-end (E2E) tests for web applications using Playwright. Invoke when user wants to create E2E tests, set up testing framework, or run automated browser tests."
---

# Web App Testing

This skill helps you set up and run end-to-end (E2E) tests for web applications using Playwright.

## When to Use

- User wants to create E2E tests for their web application
- User needs to set up automated browser testing
- User asks to test user flows and interactions
- User wants to add visual regression testing
- User needs to verify critical user journeys work correctly

## Setup Playwright

If Playwright is not already installed:

```bash
npm init playwright@latest
```

Or for existing projects:

```bash
npm install --save-dev @playwright/test
npx playwright install
```

## Configuration

Create `playwright.config.js` in project root:

```javascript
// @ts-check
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

## Test Structure

Create test files in `e2e/` directory:

```javascript
// e2e/example.spec.js
const { test, expect } = require('@playwright/test');

test('homepage has title and links', async ({ page }) => {
  await page.goto('/');
  
  // Expect a title "to contain" a substring
  await expect(page).toHaveTitle(/My App/);
  
  // Click the get started link
  await page.getByRole('link', { name: 'Get started' }).click();
  
  // Expects page to have a heading with the name of Installation
  await expect(page.getByRole('heading', { name: 'Installation' })).toBeVisible();
});
```

## Best Practices

### Use Role-Based Selectors

✅ Good:
```javascript
await page.getByRole('button', { name: 'Submit' }).click();
await page.getByLabel('Username').fill('john');
await page.getByTestId('submit-button').click();
```

❌ Avoid:
```javascript
await page.click('.btn-primary');  // Brittle class selectors
await page.fill('#username', 'john');  // ID selectors break easily
```

### Test User Flows

```javascript
test('user can complete checkout', async ({ page }) => {
  // Arrange
  await page.goto('/products');
  
  // Act
  await page.getByRole('button', { name: 'Add to cart' }).first().click();
  await page.getByRole('link', { name: 'Cart' }).click();
  await page.getByRole('button', { name: 'Checkout' }).click();
  
  // Fill form
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Card number').fill('4242424242424242');
  await page.getByRole('button', { name: 'Pay' }).click();
  
  // Assert
  await expect(page.getByText('Payment successful')).toBeVisible();
});
```

### Test Authentication

```javascript
test('authenticated user can access dashboard', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('password');
  await page.getByRole('button', { name: 'Login' }).click();
  
  // Verify redirect to dashboard
  await expect(page).toHaveURL('/dashboard');
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});
```

### Visual Regression Testing

```javascript
test('homepage visual regression', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveScreenshot('homepage.png', {
    fullPage: true,
    threshold: 0.2,
  });
});
```

### API Mocking

```javascript
test('handles API errors gracefully', async ({ page }) => {
  // Mock API failure
  await page.route('**/api/users', route => {
    route.fulfill({
      status: 500,
      body: JSON.stringify({ error: 'Server error' }),
    });
  });
  
  await page.goto('/users');
  await expect(page.getByText('Failed to load users')).toBeVisible();
});
```

## Running Tests

```bash
# Run all tests
npx playwright test

# Run in headed mode (see browser)
npx playwright test --headed

# Run specific test file
npx playwright test example.spec.js

# Run with UI mode
npx playwright test --ui

# Run in debug mode
npx playwright test --debug

# Run only failed tests
npx playwright test --last-failed

# Generate report
npx playwright show-report
```

## Common Patterns

### Page Object Model

```javascript
// e2e/pages/LoginPage.js
class LoginPage {
  constructor(page) {
    this.page = page;
    this.usernameInput = page.getByLabel('Username');
    this.passwordInput = page.getByLabel('Password');
    this.loginButton = page.getByRole('button', { name: 'Login' });
  }
  
  async goto() {
    await this.page.goto('/login');
  }
  
  async login(username, password) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }
}

module.exports = { LoginPage };
```

### Test Fixtures

```javascript
// e2e/fixtures.js
const { test: base } = require('@playwright/test');
const { LoginPage } = require('./pages/LoginPage');

const test = base.extend({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  
  // Auto-login fixture
  authenticatedPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('admin', 'password');
    await use(page);
  },
});

module.exports = { test, expect };
```

## CI/CD Integration

Add to `.github/workflows/playwright.yml`:

```yaml
name: Playwright Tests
on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
jobs:
  test:
    timeout-minutes: 60
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: lts/*
    - name: Install dependencies
      run: npm ci
    - name: Install Playwright Browsers
      run: npx playwright install --with-deps
    - name: Run Playwright tests
      run: npx playwright test
    - uses: actions/upload-artifact@v4
      if: always()
      with:
        name: playwright-report
        path: playwright-report/
        retention-days: 30
```

## Output Format

When creating tests, output:
1. Test file path
2. Test scenarios covered
3. Key selectors used
4. Any mocks or setup needed
