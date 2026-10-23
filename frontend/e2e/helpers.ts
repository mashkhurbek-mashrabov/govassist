/** Shared steps for the journey specs (role/text assertions, axe). */
import AxeBuilder from "@axe-core/playwright";
import { expect, type Page } from "@playwright/test";

/** Impacts that fail the a11y check (plan §8: 0 serious/critical). */
const BLOCKING_IMPACTS = new Set(["serious", "critical"]);
/** Seeded mock account (frontend/README.md). */
export const SEED_EMAIL = "namuna@example.com";
/** Long enough for the slowest mock stream in the browser. */
export const STREAM_TIMEOUT_MS = 20_000;

/**
 * Fail on serious or critical axe violations (WCAG 2.0/2.1/2.2 A + AA) on the current page.
 *
 * @param page The page under test.
 */
export async function expectAccessible(page: Page): Promise<void> {
  // Let entry animations finish, so contrast is not measured mid-fade (looping ones never finish).
  await page.evaluate(() =>
    Promise.all(
      document
        .getAnimations()
        .filter((animation) => animation.effect?.getComputedTiming().endTime !== Infinity)
        .map((animation) => animation.finished.catch(() => undefined)),
    ),
  );
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  const blocking = results.violations.filter((violation) => BLOCKING_IMPACTS.has(violation.impact ?? ""));
  expect(
    blocking.map(
      (violation) =>
        `${violation.id}: ${violation.help} at ${violation.nodes.map((node) => node.target.join(" ")).join(", ")}`,
    ),
  ).toEqual([]);
}

/**
 * Run an action and return the SPA path of the "[MSW mail]" link it makes the mock print.
 *
 * @param page The page under test.
 * @param action What triggers the email.
 * @returns The path, still URL-encoded as in a real email.
 */
export async function emailedPath(page: Page, action: () => Promise<void>): Promise<string> {
  const message = page.waitForEvent("console", (entry) => entry.text().startsWith("[MSW mail]"));
  await action();
  return new URL((await message).text().split(": ").at(-1) ?? "").pathname;
}

/**
 * Log in as the seeded user and wait for the chat.
 *
 * @param page The page under test.
 */
export async function logInSeedUser(page: Page): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Elektron pochta").fill(SEED_EMAIL);
  await page.getByLabel("Parol", { exact: true }).fill("namuna-parol-1");
  await page.getByRole("button", { name: "Kirish" }).click();
  await expect(page.getByRole("heading", { level: 1, name: /Salom!/ })).toBeVisible();
}

/**
 * Type a question in the composer and send it with Enter.
 *
 * @param page The page under test.
 * @param text The question.
 */
export async function ask(page: Page, text: string): Promise<void> {
  const input = page.getByLabel("Savolingiz");
  await input.fill(text);
  await input.press("Enter");
}

/**
 * Wait until `count` answers are final (their feedback bars are shown).
 *
 * @param page The page under test.
 * @param count Expected number of final answers.
 */
export async function waitForFinal(page: Page, count = 1): Promise<void> {
  await expect(page.getByText("Javob foydali boʻldimi?")).toHaveCount(count, { timeout: STREAM_TIMEOUT_MS });
}

/**
 * Click a landing header link: below 768 px the auth buttons live in the hamburger panel, so open it first.
 *
 * @param page The page.
 * @param name Link name (e.g. "Kirish").
 * @param menuLabel Accessible name of the hamburger in the current language.
 */
export async function clickLandingHeaderLink(page: Page, name: string, menuLabel: string): Promise<void> {
  await page.getByRole("heading", { level: 1 }).waitFor();
  const inBar = page.getByRole("banner").getByRole("link", { name, exact: true }).filter({ visible: true });
  if ((await inBar.count()) === 0) await page.getByRole("button", { name: menuLabel }).click();
  await page
    .getByRole("banner")
    .getByRole("link", { name, exact: true })
    .filter({ visible: true })
    .first()
    .click();
}
