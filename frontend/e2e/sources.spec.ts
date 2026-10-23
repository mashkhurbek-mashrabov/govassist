/** Contract v1.11: "list the sources" answers with the conversation's earlier citations. */
import { expect, test } from "@playwright/test";
import { ask, expectAccessible, logInSeedUser, waitForFinal } from "./helpers";

test("asking for the sources lists the conversation's earlier citations", async ({ page }) => {
  await logInSeedUser(page);
  await ask(page, "Pasportimni qanday yangilayman?");
  await waitForFinal(page);
  await ask(page, "List the sources");
  const answer = page.locator("li.assistant").last();
  await expect(
    answer.getByRole("heading", { level: 2, name: "NAMUNA: Sources of this conversation" }),
  ).toBeVisible({
    timeout: 20_000,
  });
  await waitForFinal(page, 2);
  await expect(answer.locator(".answer-head__kind")).toHaveText("Manbalar");
  await expect(answer.getByRole("link", { name: /NAMUNA xizmat sahifasi/ })).toBeVisible();
  await expect(answer.getByRole("link", { name: /NAMUNA nizom/ })).toBeVisible();
  await expect(answer.getByRole("region", { name: "Qayerga borish kerak" })).toHaveCount(0);
  await expectAccessible(page);
});
