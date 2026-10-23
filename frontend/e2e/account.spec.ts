/** Account menu in the top bar (approved addition to design v1.3). */
import { expect, test } from "@playwright/test";
import { expectAccessible, logInSeedUser } from "./helpers";

test("account menu: opens, passes axe, goes to Settings and logs out", async ({ page }) => {
  await logInSeedUser(page);
  const avatar = page.getByRole("button", { name: "Hisob menyusi" });
  await avatar.click();
  const menu = page.getByRole("menu");
  await expect(menu.getByText("namuna@example.com")).toBeVisible();
  await expect(menu.getByRole("menuitem", { name: "Sozlamalar" })).toBeFocused();
  await expectAccessible(page);
  await menu.getByRole("menuitem", { name: "Sozlamalar" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Sozlamalar" })).toBeVisible();

  await avatar.click();
  await page.getByRole("menuitem", { name: "Chiqish" }).click();
  await expect(page).toHaveURL(/\/welcome$/);
});
