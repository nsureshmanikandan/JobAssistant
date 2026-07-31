import { test, expect } from "@playwright/test";

// Requires the backend running (localhost:8010 or whatever VITE_API_BASE_URL
// points at) with at least one pending job seeded — e.g. via the manual
// paste-in form — before this test runs.
test("user can open a job, generate tailored materials, and approve it", async ({ page }) => {
  await page.goto("/");
  const firstJob = page.locator("a", { hasText: /% match/ }).first();
  await expect(firstJob).toBeVisible();
  await firstJob.click();

  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const generateButton = page.getByRole("button", { name: /generate tailored resume/i });
  if (await generateButton.isVisible()) {
    await generateButton.click();
    await expect(page.getByText(/download resume pdf/i)).toBeVisible({ timeout: 60000 });
  }

  // Approve stops here — clicking it opens the source job posting in a new tab
  // for the user to submit manually. This test verifies the button exists and
  // is clickable; it does not simulate an external site's submit flow.
  await expect(page.getByRole("button", { name: /approve/i })).toBeEnabled();
});
