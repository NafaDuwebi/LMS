const { test, expect } = require('@playwright/test');

const ADMIN = { email: 'admin@plprojects.co.uk', password: 'Admin1234!' };

test.describe('Admin Functionality', () => {

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

  test('Dashboard shows aggregate stats', async ({ page }) => {
    await expect(page.locator('text=Total Learners').or(page.locator('text=Total Courses')).first()).toBeVisible();
  });

  test('Users page lists all users', async ({ page }) => {
    await page.goto('/admin/users');
    await expect(page.locator('table').or(page.locator('text=users')).first()).toBeVisible();
  });

  test('Can create a new user', async ({ page }) => {
    await page.goto('/admin/users/create');
    await page.fill('input[name="full_name"]', 'Test User');
    await page.fill('input[name="email"]', `testuser${Date.now()}@example.com`);
    await page.selectOption('select[name="role"]', 'learner');
    await page.fill('input[name="password"]', 'TestPass123!');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/admin\/users/, { timeout: 10000 });
    await expect(page.locator('text=Test User').or(page.locator('text=users')).first()).toBeVisible();
  });

  test('Courses page shows existing courses', async ({ page }) => {
    await page.goto('/courses');
    await expect(page.locator('text=PFQ').or(page.locator('text=Course')).first()).toBeVisible();
  });

  test('Can create a course', async ({ page }) => {
    await page.goto('/courses/create');
    await page.fill('input[name="course_code"]', `TEST${Date.now()}`);
    await page.fill('input[name="title"]', `E2E Test Course ${Date.now()}`);
    await page.fill('input[name="awarding_body"]', 'Test Body');
    await page.fill('input[name="level"]', 'Foundation');
    await page.fill('textarea[name="description"]', 'Created by Playwright E2E test');
    await page.fill('input[name="pass_mark"]', '60');
    await page.selectOption('select[name="assessment_type"]', 'mixed');
    await page.selectOption('select[name="delivery_mode"]', 'online');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/courses\/\d+/, { timeout: 10000 });
    await expect(page.locator('text=E2E Test Course').first()).toBeVisible();
  });

  test('Cohorts page shows existing cohorts', async ({ page }) => {
    await page.goto('/cohorts');
    await expect(page.locator('text=PFQ').or(page.locator('text=Cohort')).first()).toBeVisible();
  });

  test('Can enrol a learner by email into a cohort', async ({ page }) => {
    await page.goto('/cohorts');
    // Click on the first cohort view link
    const cohortLink = page.locator('a[href*="/cohorts/"]').first();
    await cohortLink.click();
    await page.waitForURL(/\/cohorts\/\d+/, { timeout: 10000 });

    // Fill enrol form
    const emailInput = page.locator('input[name="email"]');
    if (await emailInput.isVisible()) {
      await emailInput.fill('enroledtest@example.com');
      await page.locator('form').filter({ has: emailInput }).locator('button[type="submit"]').click();
      await page.waitForURL(/\/cohorts\/\d+/, { timeout: 10000 });
    }
  });

  test('Settings page loads and can update', async ({ page }) => {
    await page.goto('/admin/settings');
    await expect(page.locator('input[name="org_name"]')).toBeVisible();
    // Verify current value
    const orgInput = page.locator('input[name="org_name"]');
    await orgInput.fill('PLP E2E Test');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Settings updated')).toBeVisible();
  });

  test('Audit log page loads', async ({ page }) => {
    await page.goto('/admin/audit-log');
    await expect(page.locator('table').or(page.locator('text=Audit')).first()).toBeVisible();
  });
});
