import { defineConfig, devices } from "@playwright/test";

/** Port of `npm run preview:mock`. */
const PORT = 4173;
/** Run against an already-running server instead (e.g. the nginx image serving the mock build). */
const EXTERNAL_BASE_URL = process.env.E2E_BASE_URL;

/**
 * E2E smoke on the mock build (MSW in the browser). Set `PLAYWRIGHT_CHROMIUM_PATH` to reuse a local
 * Chromium instead of `npx playwright install chromium`.
 */
export default defineConfig({
  testDir: "e2e",
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: EXTERNAL_BASE_URL ?? `http://localhost:${PORT}`,
    trace: "retain-on-failure",
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_PATH
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH }
      : {},
  },
  projects: [
    { name: "phone", use: { ...devices["Pixel 7"], viewport: { width: 375, height: 812 } } },
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
  ],
  webServer: EXTERNAL_BASE_URL
    ? undefined
    : {
        command: "npm run build:mock && npm run preview:mock",
        url: `http://localhost:${PORT}`,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
});
