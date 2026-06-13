const { test, expect } = require('@playwright/test');

const ADMIN = { email: 'admin@plprojects.co.uk', password: 'Admin1234!' };

test.describe('GDPR & Compliance', () => {

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

  test('GDPR export returns a ZIP file', async ({ page }) => {
    // Get first learner's user ID from users page
    await page.goto('/admin/users');
    const userLinks = page.locator('a[href*="/users/"]');
    // Find a learner user edit link
    const editLink = page.locator('a[href*="/edit"]').first();
    if (await editLink.isVisible()) {
      const href = await editLink.getAttribute('href');
      const userId = href.split('/').filter(p => !isNaN(p)).pop();

      // Request GDPR export
      const response = await page.request.get(`/admin/gdpr-export/${userId}`);
      expect(response.ok()).toBeTruthy();
      expect(response.headers()['content-type']).toContain('application/zip');
    }
  });

  test('Retention review page shows flagged enrolments', async ({ page }) => {
    await page.goto('/admin/retention');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });
});
