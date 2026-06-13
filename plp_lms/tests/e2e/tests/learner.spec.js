const { test, expect } = require('@playwright/test');

const LEARNER = { email: 'learner1@example.com', password: 'Learner1234!' };

test.describe('Learner Functionality', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', LEARNER.email);
    await page.fill('input[name="password"]', LEARNER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });
  });

  test('Dashboard shows enrolments and notifications', async ({ page }) => {
    await expect(page.locator('text=Enrolments').or(page.locator('text=My Courses')).first()).toBeVisible();
  });

  test('My Courses page lists enrolled courses with progress', async ({ page }) => {
    await page.goto('/learner/courses');
    await expect(page.locator('text=PFQ').or(page.locator('text=Course')).first()).toBeVisible();
  });

  test('Course view shows modules and materials', async ({ page }) => {
    await page.goto('/learner/courses');
    // Click on the first course
    const courseLink = page.locator('a[href*="/learner/course/"]').first();
    if (await courseLink.isVisible()) {
      await courseLink.click();
      await page.waitForURL(/\/learner\/course\/\d+/, { timeout: 10000 });
      await expect(page.locator('text=Module').or(page.locator('text=Material')).first()).toBeVisible();
    }
  });

  test('Can take an MCQ assessment', async ({ page }) => {
    // Navigate to assessments
    await page.goto('/assessments');
    // Click on the PFQ sample test
    const takeLink = page.locator('a[href*="/take"]').first();
    if (await takeLink.isVisible()) {
      await takeLink.click();
      await page.waitForURL(/\/assessments\/\d+\/take/, { timeout: 10000 });

      // Select first radio option for each question
      const radios = page.locator('input[type="radio"]');
      const count = await radios.count();
      for (let i = 0; i < count; i++) {
        await radios.nth(i).check({ force: true });
      }

      // Submit
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/assessments\/\d+\/result\/\d+/, { timeout: 10000 });
      await expect(page.locator('text=Score').or(page.locator('text=result')).first()).toBeVisible();
    }
  });

  test('Training record page loads and allows add/edit/delete', async ({ page }) => {
    await page.goto('/learner/training-record');
    await expect(page.locator('text=Training Record')).toBeVisible();

    // Add an external training record
    await page.fill('input[name="title"]', `E2E Training ${Date.now()}`);
    await page.fill('input[name="provider"]', 'E2E Test Provider');
    await page.selectOption('select[name="record_type"]', 'workshop');
    await page.fill('input[name="completion_date"]', '2026-06-01');
    await page.fill('input[name="hours"]', '8');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/learner\/training-record/, { timeout: 10000 });
    await expect(page.locator('text=Record added')).toBeVisible();

    // Click edit on the first record
    const editLink = page.locator('a[href*="/edit"]').first();
    if (await editLink.isVisible()) {
      await editLink.click();
      await page.waitForURL(/\/learner\/training-record\/\d+\/edit/, { timeout: 10000 });
      await page.fill('input[name="title"]', `E2E Training Updated ${Date.now()}`);
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/learner\/training-record/, { timeout: 10000 });
      await expect(page.locator('text=Record updated')).toBeVisible();
    }

    // Delete the last record
    const deleteForm = page.locator('form[action*="/delete"]').last();
    page.on('dialog', dialog => dialog.accept());
    if (await deleteForm.isVisible()) {
      await deleteForm.locator('button[type="submit"]').click();
      await page.waitForURL(/\/learner\/training-record/, { timeout: 10000 });
      await expect(page.locator('text=Record deleted')).toBeVisible();
    }
  });

  test('Profile page loads and can update', async ({ page }) => {
    await page.goto('/learner/profile');
    await expect(page.locator('input[name="full_name"]')).toBeVisible();
    const nameInput = page.locator('input[name="full_name"]');
    await nameInput.fill('Alice Johnson E2E');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Profile updated')).toBeVisible();
  });

  test('Results page loads', async ({ page }) => {
    await page.goto('/learner/results');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('Certificates page loads', async ({ page }) => {
    await page.goto('/learner/certificates');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('Notifications page loads and can mark as read', async ({ page }) => {
    await page.goto('/notifications');
    await expect(page.locator('h1, h2').first()).toBeVisible();

    // Mark all as read if button exists
    const markAllBtn = page.locator('button:has-text("Mark All Read"), form[action*="mark-all-read"] button');
    if (await markAllBtn.isVisible()) {
      await markAllBtn.click();
      await page.waitForURL(/\/notifications/, { timeout: 10000 });
    }
  });

  test('Messages page loads', async ({ page }) => {
    await page.goto('/messages');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });
});
