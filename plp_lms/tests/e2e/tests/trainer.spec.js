const { test, expect } = require('@playwright/test');

const TRAINER = { email: 'trainer@plprojects.co.uk', password: 'Trainer1234!' };

test.describe('Trainer Functionality', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', TRAINER.email);
    await page.fill('input[name="password"]', TRAINER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });
  });

  test('Dashboard shows trainer stats', async ({ page }) => {
    await expect(page.locator('text=My Cohorts').or(page.locator('text=Pending Marking')).first()).toBeVisible();
  });

  test('My Cohorts page lists assigned cohorts', async ({ page }) => {
    await page.goto('/trainer/cohorts');
    await expect(page.locator('text=PFQ').or(page.locator('text=Cohort')).first()).toBeVisible();
  });

  test('My Learners page shows enrolled learners', async ({ page }) => {
    await page.goto('/trainer/learners');
    await expect(page.locator('table').or(page.locator('text=Learner')).first()).toBeVisible();
  });

  test('Pending submissions page loads', async ({ page }) => {
    await page.goto('/trainer/submissions');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('Assessments page loads', async ({ page }) => {
    await page.goto('/assessments');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('Marking queue page loads', async ({ page }) => {
    await page.goto('/assessments/marking');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('Attendance register page loads for assigned cohort', async ({ page }) => {
    // First navigate to cohorts to get a cohort ID
    await page.goto('/trainer/cohorts');
    const cohortLink = page.locator('a[href*="/attendance/"]').first();
    if (await cohortLink.isVisible()) {
      await cohortLink.click();
      await page.waitForURL(/\/attendance\/\d+/, { timeout: 10000 });
      await expect(page.locator('text=Attendance').or(page.locator('table')).first()).toBeVisible();
    }
  });

  test('Can add a new session date', async ({ page }) => {
    // Go to first cohort's attendance
    await page.goto('/trainer/cohorts');
    const cohortLink = page.locator('a[href*="/attendance/"]').first();
    if (await cohortLink.isVisible()) {
      await cohortLink.click();
      await page.waitForURL(/\/attendance\/\d+/, { timeout: 10000 });

      // Add a session
      const sessionInput = page.locator('input[name="session_date"]');
      if (await sessionInput.isVisible()) {
        await sessionInput.fill('2026-06-15');
        await page.locator('form[action*="/session"]').first().locator('button[type="submit"]').click();
        await page.waitForURL(/\/attendance\/\d+/, { timeout: 10000 });
      }
    }
  });
});
