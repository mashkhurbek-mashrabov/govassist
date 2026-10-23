/** Design v1.2: the language menu on the landing and in the app, and the landing's streaming preview. */
import { expect, test, type Page } from "@playwright/test";
import { expectAccessible, logInSeedUser } from "./helpers";

/** Below this width the menu is a bottom sheet. */
const PHONE_MAX_WIDTH = 767;

/**
 * Whether the test runs at phone width.
 *
 * @param page The page.
 * @returns `true` for the phone project.
 */
function isPhone(page: Page): boolean {
  return (page.viewportSize()?.width ?? 0) <= PHONE_MAX_WIDTH;
}

test("landing: switch the language from the keyboard; the choice survives a reload", async ({ page }) => {
  await page.goto("/welcome");
  await expect(
    page.getByRole("heading", { level: 1, name: "Qaysi hujjat, qaysi idora — aniq javob." }),
  ).toBeVisible();
  await expectAccessible(page);

  const button = page.getByRole("banner").getByRole("button", { name: /Tilni tanlash/ });
  await button.focus();
  await page.keyboard.press("ArrowDown");
  const menu = page.getByRole("menu");
  await expect(menu).toBeVisible();
  await expect(menu.getByRole("menuitemradio", { name: /Oʻzbekcha/ })).toBeFocused();
  const viewport = page.viewportSize();
  if (isPhone(page)) {
    // Bottom sheet: pinned to the bottom edge, full width (polled: it slides in).
    await expect
      .poll(async () => {
        const box = await menu.boundingBox();
        return [Math.round((box?.y ?? 0) + (box?.height ?? 0)), Math.round(box?.width ?? 0)];
      })
      .toEqual([viewport?.height, viewport?.width]);
  } else {
    // Popover under the button.
    const buttonBox = await button.boundingBox();
    await expect.poll(async () => (await menu.boundingBox())?.y ?? 0).toBeGreaterThan(buttonBox?.y ?? 0);
  }
  await expectAccessible(page);

  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("heading", { level: 1, name: "Какие документы, какое учреждение — точный ответ." }),
  ).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("lang", "ru");
  const switched = page.getByRole("banner").getByRole("button", { name: /Выбрать язык/ });
  await expect(switched).toContainText("RU");
  await expect(switched).toBeFocused();
  await expect(page.getByRole("status").filter({ hasText: "Язык изменён" })).toHaveCount(1);

  await page.reload();
  await expect(page.getByRole("heading", { level: 1, name: /Какие документы/ })).toBeVisible();
  await expectAccessible(page);
});

test("app: the sidebar menu switches the UI and saves it to the profile", async ({ page }) => {
  await logInSeedUser(page);
  if (isPhone(page)) await page.getByRole("button", { name: "Menyu" }).click();
  const sidebar = page.getByRole("complementary");
  await sidebar.getByRole("button", { name: /Tilni tanlash/ }).click();
  const saved = page.waitForResponse(
    (response) => response.url().endsWith("/api/v1/me") && response.request().method() === "PATCH",
  );
  await page.getByRole("menuitemradio", { name: /English/ }).click();
  expect((await saved).ok()).toBe(true);
  await expect(page.getByRole("heading", { level: 1, name: /Hi!/ })).toBeVisible();
  await expectAccessible(page);

  await page.reload();
  await expect(page.getByRole("heading", { level: 1, name: /Hi!/ })).toBeVisible();
  await page.goto("/settings");
  await expect(page.getByRole("radio", { name: /English/ })).toBeChecked();
  await expectAccessible(page);
});

test("landing preview streams by itself, and shows the finished card under reduced motion", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto("/welcome");
  const preview = page.getByRole("figure");
  // It only plays on screen (below the fold on phones).
  await preview.scrollIntoViewIfNeeded();
  await expect(preview).toHaveAttribute("data-playing", "");
  const running = await page.evaluate(
    () =>
      document
        .getAnimations()
        .filter(
          (animation) => "animationName" in animation && String(animation.animationName).startsWith("pp-"),
        ).length,
  );
  expect(running).toBeGreaterThan(0);

  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.reload();
  await expect(preview.locator(".pp-progress")).toBeHidden();
  for (const part of [".pp-summary", ".pp-step-3", ".pp-office"]) {
    await expect(preview.locator(part)).toHaveCSS("opacity", "1");
  }
});
