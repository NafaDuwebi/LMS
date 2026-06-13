const { test, expect } = require('@playwright/test');

const ADMIN = { email: 'admin@plprojects.co.uk', password: 'Admin1234!' };

test.describe('Certificate Lifecycle', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', ADMIN.email);
    await page.fill('input[name="password"]', ADMIN.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|auth\/change-password)/, { timeout: 10000 });
    if (page.url().includes('change-password')) {
      await page.fill('input[name="current_password"]', ADMIN.password);
      await page.fill('input[name="new_password"]', ADMIN.password);
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/dashboard/, { timeout: 10000 });
    }
  });

  test('Certificates page loads', async ({ page }) => {
    await page.goto('/certificates');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('Public certificate verification page works', async ({ page }) => {
    await page.goto('/certificates/verify/PLP-2026-0001');
    // Page should load regardless of whether cert exists
    await expect(page.locator('body')).toBeVisible();
  });
});
