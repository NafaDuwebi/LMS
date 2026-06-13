const { test, expect } = require('@playwright/test');

const ADMIN = { email: 'admin@plprojects.co.uk', password: 'Admin1234!' };

test.describe('Reports', () => {

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

  test('Reports page loads', async ({ page }) => {
    await page.goto('/reports');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('Cohort summary report returns JSON', async ({ page }) => {
    // Get the first cohort ID from cohorts page
    await page.goto('/cohorts');
    const cohortLink = page.locator('a[href*="/cohorts/"]').first();
    if (await cohortLink.isVisible()) {
      const href = await cohortLink.getAttribute('href');
      const cohortId = href.split('/').pop();

      // Access cohort summary report
      const response = await page.request.get(`/reports/cohort-summary/${cohortId}`);
      expect(response.ok()).toBeTruthy();
      const data = await response.json();
      expect(Array.isArray(data)).toBeTruthy();
    }
  });

  test('Certificate register report returns JSON', async ({ page }) => {
    const response = await page.request.get('/reports/certificate-register');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
  });

  test('Compliance report returns JSON', async ({ page }) => {
    const response = await page.request.get('/reports/compliance');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
  });

  test('Compliance CSV downloads', async ({ page }) => {
    const response = await page.request.get('/reports/compliance/csv');
    expect(response.ok()).toBeTruthy();
    expect(response.headers()['content-type']).toContain('text/csv');
  });
});
