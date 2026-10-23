/** Design v1.3 landing: header nav vs hamburger, the responsive comparison, carrying a tile's question. */
import { expect, test, type Page } from "@playwright/test";
import { expectAccessible } from "./helpers";

/** The inline section nav replaces the hamburger from this width. */
const DESKTOP_MIN_WIDTH = 1280;
/** Below this width the comparison rows are cards. */
const PHONE_MAX_WIDTH = 767;

/**
 * The viewport width.
 *
 * @param page The page.
 * @returns Width in px.
 */
function width(page: Page): number {
  return page.viewportSize()?.width ?? 0;
}

test("header: inline nav on desktop, a hamburger panel below that closes on Esc", async ({ page }) => {
  await page.goto("/welcome");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const toggle = page.getByRole("button", { name: "Menyuni ochish" });
  if (width(page) >= DESKTOP_MIN_WIDTH) {
    await expect(
      page.getByRole("banner").getByRole("navigation", { name: "Sahifa boʻlimlari" }),
    ).toBeVisible();
    await expect(toggle).toBeHidden();
    return;
  }
  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  const panel = page.locator(`[id="${(await toggle.getAttribute("aria-controls")) ?? ""}"]`);
  await expect(panel.getByRole("link", { name: "Roʻyxatdan oʻtish" })).toBeVisible();
  await expectAccessible(page);
  await page.keyboard.press("Escape");
  await expect(panel).toBeHidden();
  await expect(toggle).toBeFocused();
  await toggle.click();
  await panel.getByRole("link", { name: "Nega GovAssist" }).click();
  await expect(panel).toBeHidden();
  await expect(page.getByRole("heading", { name: "GovAssist va oddiy chatbot" })).toBeInViewport();
});

test("comparison: a table on desktop, stacked cards on phones", async ({ page }) => {
  await page.goto("/welcome");
  const table = page.getByRole("table", { name: "GovAssist va oddiy chatbot" });
  await table.scrollIntoViewIfNeeded();
  const firstRow = table.locator("tbody tr").first();
  if (width(page) <= PHONE_MAX_WIDTH) {
    await expect(firstRow).toHaveCSS("display", "block");
    await expect(firstRow.locator(".lp-compare__tag").first()).toBeVisible();
  } else {
    await expect(firstRow).toHaveCSS("display", "table-row");
    await expect(firstRow.locator(".lp-compare__tag").first()).toBeHidden();
  }
  await expect(table.getByRole("rowheader")).toHaveCount(5);
  await expectAccessible(page);
});

test("a service tile carries its question to sign-up without putting it in the URL", async ({ page }) => {
  await page.goto("/welcome");
  await page
    .getByRole("region", { name: "Ommabop xizmatlar" })
    .getByRole("link", { name: /Pensiya/ })
    .click();
  await expect(page).toHaveURL(/\/signup$/);
  await expect(page.locator("q.carried__q")).toHaveText("Pensiya tayinlash uchun qanday hujjatlar kerak?");
  await expectAccessible(page);
});
