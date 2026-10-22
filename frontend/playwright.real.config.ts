import { defineConfig, devices } from "@playwright/test";

/**
 * E2E against the real backend (F3): `invoke up` in the repo root, then `npm run dev` with
 * `VITE_USE_MOCKS=false` and the Turnstile test key. Answers come from Gemini, so this runs locally, not in CI.
 * Set `PLAYWRIGHT_CHROMIUM_PATH` to reuse a local Chromium.
 */
export default defineConfig({
  testDir: "e2e/real",
  timeout: 240_000,
  workers: 1,
  reporter: "list",
  outputDir: "test-results-real",
  use: {
    baseURL: process.env.E2E_REAL_BASE_URL ?? "http://localhost:5173",
    trace: "retain-on-failure",
    // Steady screenshots: no entry fades mid-capture.
    contextOptions: { reducedMotion: "reduce" },
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_PATH
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH }
      : {},
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
  ],
});
