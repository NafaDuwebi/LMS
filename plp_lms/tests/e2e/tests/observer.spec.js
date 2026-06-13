const { test, expect } = require('@playwright/test');

const OBSERVER = { email: 'observer@plprojects.co.uk', password: 'Observer1234!' };

test.describe('Observer Functionality', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', OBSERVER.email);
    await page.fill('input[name="password"]', OBSERVER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });
  });

  test('Dashboard shows active cohorts', async ({ page }) => {
    await expect(page.locator('text=Cohorts').or(page.locator('table')).first()).toBeVisible();
  });

  test('Can view courses list', async ({ page }) => {
    await page.goto('/courses');
    await expect(page.locator('text=PFQ').or(page.locator('text=Course')).first()).toBeVisible();
  });

  test('Can view cohorts list', async ({ page }) => {
    await page.goto('/cohorts');
    await expect(page.locator('text=PFQ').or(page.locator('text=Cohort')).first()).toBeVisible();
  });

  test('Can view reports page', async ({ page }) => {
    await page.goto('/reports');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });
});
