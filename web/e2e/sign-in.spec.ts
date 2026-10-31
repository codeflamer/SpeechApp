import { expect, test } from "@playwright/test";

import { waitForSignInLink } from "./mailpit";

test("signed-out visitors are sent to sign-in", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/sign-in$/);
  await expect(page.getByRole("heading", { name: "Sign in to Maple" })).toBeVisible();
});

test("sign in with an email link, then sign out", async ({ page }) => {
  // A fresh address each run, so earlier emails in the inbox can't be picked up by mistake.
  const email = `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;

  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Send sign-in link" }).click();
  await expect(page.getByRole("status")).toContainText(email);

  await page.goto(await waitForSignInLink(email));
  await expect(page).toHaveURL("/");
  await expect(page.getByTestId("signed-in-as")).toContainText(email);

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/sign-in$/);
  await page.goto("/");
  await expect(page).toHaveURL(/\/sign-in$/);
});

test("the link works in a different browser than the one that asked for it", async ({ page, browser }) => {
  // Learners often request the link on a laptop and tap it in their phone's mail app.
  const email = `e2e-xb-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Send sign-in link" }).click();
  await expect(page.getByRole("status")).toContainText(email);
  const link = await waitForSignInLink(email);

  const otherBrowser = await browser.newContext(); // no cookies from the first browser
  const otherPage = await otherBrowser.newPage();
  await otherPage.goto(link);
  await expect(otherPage.getByTestId("signed-in-as")).toContainText(email);
  await otherBrowser.close();
});

test("a used or bad link shows a friendly message", async ({ page }) => {
  await page.goto("/auth/confirm?token_hash=not-a-real-token&type=email");
  await expect(page).toHaveURL(/\/sign-in\?error=link$/);
  // Next.js adds its own empty role="alert" route announcer, so match ours by text.
  await expect(page.getByRole("alert").filter({ hasText: "expired" })).toContainText("Request a new one");
});
