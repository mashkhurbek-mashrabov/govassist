import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

/** Impacts that fail the a11y check (plan §8). */
const BLOCKING_IMPACTS = new Set(["serious", "critical"]);

/**
 * Fail on serious or critical axe violations on the current page.
 *
 * @param page The page under test.
 */
async function expectAccessible(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page }).analyze();
  const blocking = results.violations.filter((violation) => BLOCKING_IMPACTS.has(violation.impact ?? ""));
  expect(blocking.map((violation) => `${violation.id}: ${violation.help}`)).toEqual([]);
}

/**
 * Wait for the next "[MSW mail]" console line and return the link it prints.
 *
 * @param page The page under test.
 * @param action What triggers the email.
 * @returns The SPA path from the logged link.
 */
async function emailedPath(page: Page, action: () => Promise<void>): Promise<string> {
  const message = page.waitForEvent("console", (entry) => entry.text().startsWith("[MSW mail]"));
  await action();
  return new URL((await message).text().split(": ").at(-1) ?? "").pathname;
}

/** The whole F1 journey on mocks, in the default language (uz-Latn). */
test("signup → verify → onboarding → streamed answer, stop/retry → feedback → history → settings", async ({
  page,
}) => {
  const email = `e2e-${Date.now()}@example.com`;

  await page.goto("/signup");
  await expectAccessible(page);
  await page.getByLabel("Elektron pochta").fill(email);
  await page.getByLabel("Parol", { exact: true }).fill("namuna-parol-123");
  const verifyPath = await emailedPath(page, () =>
    page.getByRole("button", { name: "Roʻyxatdan oʻtish" }).click(),
  );
  await expect(page).toHaveURL(/\/check-email$/);

  await page.goto(verifyPath);
  await page.getByRole("button", { name: "Tasdiqlash" }).click();
  await expect(page).toHaveURL(/\/onboarding$/);
  await expectAccessible(page);

  await page.getByLabel("Viloyat").selectOption({ label: "Toshkent shahri" });
  await page.getByLabel("Tuman").selectOption({ label: "Chilonzor tumani" });
  await page.getByRole("button", { name: "Davom etish" }).click();
  await expect(page.getByRole("heading", { name: "Davlat xizmati yoki qonun haqida soʻrang" })).toBeVisible();
  await expectAccessible(page);

  const input = page.getByLabel("Savolingiz");
  await input.fill("Pasportimni qanday yangilayman?");
  await input.press("Enter");
  await expect(page).toHaveURL(/\/c\/[0-9a-f-]+$/);
  await expect(page.getByRole("button", { name: "Toʻxtatish" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Idora" })).toContainText("NAMUNA Chilonzor");
  await expect(page.getByRole("heading", { name: "Manbalar" })).toBeVisible();
  await expect(page.getByRole("link", { name: "1-manba" }).first()).toBeVisible();
  await expect(input).toBeFocused();
  await expectAccessible(page);

  await page.getByRole("button", { name: "Foydali", exact: true }).click();
  await expect(page.getByText("Rahmat, fikringiz saqlandi.")).toBeVisible();

  await input.fill("Pasportni onlayn almashtirsa boʻladimi?");
  await page.getByRole("button", { name: "Yuborish", exact: true }).click();
  await page.getByRole("button", { name: "Toʻxtatish" }).click();
  await expect(page.getByText("Siz bu javobni toʻxtatdingiz.")).toBeVisible();
  await page.getByRole("button", { name: "Qayta urinish" }).click();
  await expect(page.getByRole("button", { name: "Yuborish", exact: true })).toBeVisible();
  await expect(page.getByText("Siz bu javobni toʻxtatdingiz.")).toHaveCount(0);

  await page.goto("/history");
  await expect(page.getByRole("link", { name: /Pasportimni qanday yangilayman/ })).toBeVisible();
  await expectAccessible(page);

  await page.goto("/settings");
  await expect(page.getByText("Shu soatda: 20 tadan 3 ta")).toBeVisible();
  await expectAccessible(page);
  await page.getByLabel("Til").selectOption({ label: "English" });
  await page.getByRole("button", { name: "Saqlash" }).click();
  await expect(page.getByRole("heading", { name: "Settings", level: 1 })).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page).toHaveURL(/\/login$/);
});

/** Pre-stream errors show the contract message with retry_after. */
test("rate limit shows the retry time", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Elektron pochta").fill("namuna@example.com");
  await page.getByLabel("Parol", { exact: true }).fill("any-password-1");
  await page.getByRole("button", { name: "Kirish" }).click();
  await page.getByLabel("Savolingiz").fill("Savol #limit");
  await page.getByLabel("Savolingiz").press("Enter");
  await expect(page.getByText("21 daqiqadan keyin qayta urinib koʻring")).toBeVisible();
});
