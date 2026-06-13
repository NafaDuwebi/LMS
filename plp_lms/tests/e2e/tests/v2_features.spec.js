const { test, expect } = require('@playwright/test');

const ADMIN = { email: 'admin@plprojects.co.uk', password: 'Admin1234!' };
const LEARNER = { email: 'learner1@example.com', password: 'Learner1234!' };

test.describe('v2.1 Features — Admin', () => {

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

  test('Learning paths page loads', async ({ page }) => {
    await page.goto('/learning-paths');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('Can create a learning path and add a course', async ({ page }) => {
    await page.goto('/learning-paths/create');
    await page.fill('input[name="title"]', `E2E Path ${Date.now()}`);
    await page.fill('textarea[name="description"]', 'Created by Playwright E2E test');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/learning-paths\/\d+/, { timeout: 10000 });
    await expect(page.locator('text=E2E Path').first()).toBeVisible();
  });

  test('Skills management page loads for PFQ course', async ({ page }) => {
    // Get PFQ course ID from courses page
    await page.goto('/courses');
    const courseLink = page.locator('a[href*="/courses/"]').first();
    if (await courseLink.isVisible()) {
      const href = await courseLink.getAttribute('href');
      const courseId = href.split('/').pop();
      await page.goto(`/skills/manage/${courseId}`);
      await expect(page.locator('h1, h2').first()).toBeVisible();
    }
  });

  test('Can create a skill', async ({ page }) => {
    await page.goto('/courses');
    const courseLink = page.locator('a[href*="/courses/"]').first();
    if (await courseLink.isVisible()) {
      const href = await courseLink.getAttribute('href');
      const courseId = href.split('/').pop();
      await page.goto(`/skills/manage/${courseId}`);
      await page.fill('input[name="title"]', `E2E Skill ${Date.now()}`);
      await page.fill('textarea[name="description"]', 'E2E test skill');
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/skills\/manage\/\d+/, { timeout: 10000 });
      await expect(page.locator('text=E2E Skill').first()).toBeVisible();
    }
  });

  test('Skills review page loads', async ({ page }) => {
    await page.goto('/skills/review');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('Document requirements page loads for a cohort', async ({ page }) => {
    await page.goto('/cohorts');
    const cohortLink = page.locator('a[href*="/cohorts/"]').first();
    if (await cohortLink.isVisible()) {
      const href = await cohortLink.getAttribute('href');
      const cohortId = href.split('/').pop();
      await page.goto(`/documents/requirements/${cohortId}`);
      await expect(page.locator('h1, h2').first()).toBeVisible();
    }
  });

  test('Document review queue loads', async ({ page }) => {
    await page.goto('/documents/review');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('RPL review queue loads', async ({ page }) => {
    await page.goto('/rpl/review');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('Retention review page loads', async ({ page }) => {
    await page.goto('/admin/retention');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('Report subscriptions page loads', async ({ page }) => {
    await page.goto('/reports/subscriptions');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('Can create a report subscription', async ({ page }) => {
    await page.goto('/reports/subscriptions');
    const createBtn = page.locator('a[href*="/subscriptions"], button:has-text("Create")').first();
    if (await createBtn.isVisible()) {
      await createBtn.click();
    }
    // If there's a form on the page
    const reportIdInput = page.locator('select[name="report_id"]');
    if (await reportIdInput.isVisible()) {
      await reportIdInput.selectOption({ index: 0 });
      await page.fill('input[name="recipient_emails"]', 'admin@plprojects.co.uk');
      await page.selectOption('select[name="frequency"]', 'weekly');
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/reports\/subscriptions/, { timeout: 10000 });
    }
  });
});

test.describe('v2.1 Features — Learner', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', LEARNER.email);
    await page.fill('input[name="password"]', LEARNER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });
  });

  test('Learning paths page loads for learner', async ({ page }) => {
    await page.goto('/learning-paths');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('My skills page loads', async ({ page }) => {
    await page.goto('/skills/my');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('Document upload page loads for PFQ cohort', async ({ page }) => {
    await page.goto('/cohorts');
    const cohortLink = page.locator('a[href*="/documents/upload/"]').first();
    if (await cohortLink.isVisible()) {
      await cohortLink.click();
      await page.waitForURL(/\/documents\/upload\/\d+/, { timeout: 10000 });
      await expect(page.locator('h1, h2').first()).toBeVisible();
    }
  });

  test('Can submit an RPL claim', async ({ page }) => {
    // Get a course ID
    await page.goto('/courses');
    const courseLink = page.locator('a[href*="/courses/"]').first();
    if (await courseLink.isVisible()) {
      const href = await courseLink.getAttribute('href');
      const courseId = href.split('/').pop();
      await page.goto(`/rpl/claim/${courseId}`);
      await expect(page.locator('input[name="prior_title"]')).toBeVisible();
      await page.fill('input[name="prior_title"]', `E2E RPL Claim ${Date.now()}`);
      await page.fill('input[name="prior_provider"]', 'E2E Provider');
      await page.fill('input[name="completion_date"]', '2025-01-01');
      await page.fill('textarea[name="statement"]', 'E2E test RPL claim statement');
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/learner\/training-record/, { timeout: 10000 });
    }
  });
});
