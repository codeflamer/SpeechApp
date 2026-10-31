import { defineConfig, devices } from "@playwright/test";

// E2E tests run against the local Supabase stack (`npm run db:start` at the repo root).
// Locally they reuse `npm run dev` if it's already running; CI builds and starts the app.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: process.env.CI ? "npm run start" : "npm run dev",
    url: "http://localhost:3000/sign-in",
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
});
