import { defineConfig } from "@playwright/test";

// End-to-end tests drive a running app: set E2E_BASE_URL (default http://localhost:3000),
// E2E_API_URL (default http://localhost:8000) and a confirmed test account in
// E2E_EMAIL / E2E_PASSWORD. They use real AI calls, so they are run on demand
// (`npm run test:e2e`), not on every push. E2E_CHROME=0 uses Playwright's own browser
// instead of the Chrome installed on the machine.
export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 5 * 60_000,
  expect: { timeout: 30_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    channel: process.env.E2E_CHROME === "0" ? undefined : "chrome",
    trace: "retain-on-failure",
  },
});
