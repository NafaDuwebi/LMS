const { test, expect } = require('@playwright/test');

const ADMIN = { email: 'admin@plprojects.co.uk', password: 'Admin1234!' };
const TRAINER = { email: 'trainer@plprojects.co.uk', password: 'Trainer1234!' };
const LEARNER = { email: 'learner1@example.com', password: 'Learner1234!' };
const OBSERVER = { email: 'observer@plprojects.co.uk', password: 'Observer1234!' };

test.describe('Authentication', () => {

  test('Login page loads', async ({ page }) => {
    await page.goto('/auth/login');
    await expect(page.locator('h1, h2').first()).toBeVisible();
    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test('Register page loads', async ({ page }) => {
    await page.goto('/auth/register');
    await expect(page.locator('input[name="full_name"]')).toBeVisible();
  });

  test('Admin login succeeds and redirects to dashboard', async ({ page }) => {
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', ADMIN.email);
    await page.fill('input[name="password"]', ADMIN.password);
    await page.click('button[type="submit"]');
    // May redirect to change-password on first login, then to dashboard
    await page.waitForURL(/\/(dashboard|auth\/change-password)/, { timeout: 10000 });
    if (page.url().includes('change-password')) {
      await page.fill('input[name="current_password"]', ADMIN.password);
      await page.fill('input[name="new_password"]', ADMIN.password);
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/dashboard/, { timeout: 10000 });
    }
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('Trainer login succeeds', async ({ page }) => {
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', TRAINER.email);
    await page.fill('input[name="password"]', TRAINER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('Learner login succeeds', async ({ page }) => {
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', LEARNER.email);
    await page.fill('input[name="password"]', LEARNER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('Observer login succeeds', async ({ page }) => {
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', OBSERVER.email);
    await page.fill('input[name="password"]', OBSERVER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('Invalid credentials shows error', async ({ page }) => {
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', 'nobody@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
  });

  test('Logout clears session', async ({ page }) => {
    await page.goto('/auth/login');
    await page.fill('input[name="username"]', LEARNER.email);
    await page.fill('input[name="password"]', LEARNER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });

    await page.click('a[href="/auth/logout"]');
    await page.waitForURL(/\/auth\/login/, { timeout: 10000 });
    await expect(page).toHaveURL(/\/auth\/login/);

    // Ensure cannot access dashboard without session
    await page.goto('/dashboard');
    await page.waitForURL(/\/auth\/login/, { timeout: 10000 });
  });
});
