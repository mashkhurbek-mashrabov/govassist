import { expect, test } from "@playwright/test";
import {
  STREAM_TIMEOUT_MS,
  ask,
  clickLandingHeaderLink,
  emailedPath,
  expectAccessible,
  logInSeedUser,
  waitForFinal,
} from "./helpers";

/** J1–J6 from docs/design/screens.md on the mock build, at 375 and 1440 (projects). */

test("J1 · new user: landing question → sign up → verify → onboarding → that question streams → 👍 → follow-up", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/welcome$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(/Qaysi hujjat, qaysi idora/);
  await expectAccessible(page);

  // v1.3: ask on the landing; the question is carried to sign-up in sessionStorage, never in the URL.
  await page.getByRole("textbox", { name: /Savolingizni yozing/ }).fill("Pasportimni qanday yangilayman?");
  await page.getByRole("button", { name: "Soʻrash" }).click();
  await expect(page.getByRole("heading", { name: "Roʻyxatdan oʻting" })).toBeVisible();
  await expect(page).toHaveURL(/\/signup$/);
  await expect(page.getByText("Savolingiz saqlandi")).toBeVisible();
  await expect(page.locator("q.carried__q")).toHaveText("Pasportimni qanday yangilayman?");
  await page.getByLabel("Elektron pochta").fill(`j1-${Date.now()}@example.com`);
  await page.getByLabel("Parol", { exact: true }).fill("Namuna-parol-123");
  await expect(page.getByText("kuchli")).toBeVisible();
  await expectAccessible(page);
  const verifyPath = await emailedPath(page, () =>
    page.getByRole("button", { name: "Hisob yaratish" }).click(),
  );
  await expect(page.getByRole("heading", { name: "Pochtangizni tekshiring" })).toBeVisible();
  await expectAccessible(page);

  await page.goto(verifyPath);
  await expect(page.getByRole("heading", { name: "Elektron pochta tasdiqlandi" })).toBeVisible();
  await page.getByRole("button", { name: "Davom etish" }).click();

  await expect(page.getByRole("heading", { name: "Qaysi tilda gaplashamiz?" })).toBeVisible();
  await expectAccessible(page);
  await page.getByRole("button", { name: "Keyingi" }).click();
  await page.getByRole("combobox", { name: "Viloyat" }).click();
  await page.getByRole("option", { name: "Toshkent shahri" }).click();
  await page.getByRole("combobox", { name: "Tuman yoki shahar" }).fill("Чил");
  await page.getByRole("option", { name: "Chilonzor tumani" }).click();
  await expectAccessible(page);
  await page.getByRole("button", { name: "Saqlash va boshlash" }).click();

  // The carried question is the first chat message, sent by itself.
  await expect(page.locator("li.msg-user")).toHaveText(/Pasportimni qanday yangilayman\?/);
  await expect(
    page
      .getByRole("status")
      .filter({ hasText: /Hujjatlar qidirilmoqda|manba topildi|Javob yozilmoqda/ })
      .first(),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/c\/[0-9a-f-]+$/);
  await expect(page.getByRole("region", { name: "Qayerga borish kerak" })).toBeVisible();
  await waitForFinal(page);
  await expect(page.getByRole("heading", { name: "Manbalar" })).toBeVisible();
  expect(await page.evaluate(() => sessionStorage.getItem("govassist.pendingQuestion"))).toBeNull();
  await expectAccessible(page);

  await page.getByRole("button", { name: "Ha, foydali" }).click();
  await expect(page.getByText("Rahmat! Fikringiz saqlandi.")).toBeVisible();
  await page.getByRole("button", { name: "Pasportni onlayn almashtirsa boʻladimi?" }).click();
  await waitForFinal(page, 2);
  await expect(page.getByRole("heading", { name: "NAMUNA: Pasportni onlayn almashtirish" })).toBeVisible();
});

test("J2 · returning user: log in → Cyrillic labour-law question → legal answer → open a source", async ({
  page,
}) => {
  await page.goto("/welcome");
  await clickLandingHeaderLink(page, "Kirish", "Menyuni ochish");
  await logInSeedUser(page);
  await ask(page, "NAMUNA: Йиллик меҳнат таътили ҳақида қонунда нима дейилган?");
  await waitForFinal(page);
  await expect(page.getByRole("heading", { level: 2, name: "NAMUNA: Йиллик меҳнат таътили" })).toBeVisible();
  await expect(page.getByText("Huquqiy savol")).toBeVisible();
  await expect(page.getByText("Qonun matni")).toHaveCount(2);
  await expectAccessible(page);
  await page.getByRole("link", { name: "1-manba" }).first().click();
  await expect(page).toHaveURL(/#source-.+-S1$/);
  await expect(page.locator(":target")).toContainText("NAMUNA Mehnat kodeksi");
});

test("J3 · Russian question: region fallback with unknown hours → Google Maps in a new tab", async ({
  page,
}) => {
  await logInSeedUser(page);
  await ask(page, "NAMUNA: Как зарегистрироваться по месту жительства?");
  await waitForFinal(page);
  await expect(
    page.getByRole("heading", { level: 2, name: "NAMUNA: Регистрация по месту жительства" }),
  ).toBeVisible();
  const office = page.getByRole("region", { name: "Qayerga borish kerak" });
  await expect(office.getByText(/hududingizdagi boshqa idora/)).toBeVisible();
  await expect(office.getByText("Ish vaqti nomaʼlum")).toBeVisible();
  await expect(office.getByText("Telefon raqami nomaʼlum")).toBeVisible();
  await expect(page.getByText("Manbalarda koʻrsatilmagan")).toBeVisible();
  const map = office.getByRole("link", { name: /Google Xaritada ochish/ });
  await expect(map).toHaveAttribute("target", "_blank");
  await expect(map).toHaveAttribute("rel", "noopener noreferrer");
  await expectAccessible(page);
});

test("J4 · off topic (early office withdrawn) → topic → not found → rephrase → office in the lunch break", async ({
  page,
}) => {
  // A Thursday 13:30 in Tashkent: inside the 13:00–14:00 break.
  await page.clock.setFixedTime(new Date("2026-10-22T13:30:00+05:00"));
  await logInSeedUser(page);
  // Contract v1.7: this off-topic question still gets an early office event; the refused answer drops it.
  await ask(page, "NAMUNA: Idora oldida ertaga ob-havo qanday boʻladi?");
  await expect(page.getByText(/davlat xizmatlari va Oʻzbekiston qonunlari/)).toBeVisible({
    timeout: STREAM_TIMEOUT_MS,
  });
  await waitForFinal(page);
  await expect(page.getByRole("region", { name: "Qayerga borish kerak" })).toHaveCount(0);
  await expectAccessible(page);
  await page.getByRole("button", { name: "NAMUNA savol: tugʻilganlik haqida guvohnoma" }).click();
  await expect(page.getByRole("heading", { name: "NAMUNA: aniq javob topilmadi" })).toBeVisible({
    timeout: STREAM_TIMEOUT_MS,
  });
  await waitForFinal(page, 2);
  await ask(page, "NAMUNA: Bolamga tugʻilganlik haqida guvohnomani qanday olaman?");
  await expect(
    page.getByRole("heading", { name: "NAMUNA: Tugʻilganlik haqida guvohnoma olish" }),
  ).toBeVisible({
    timeout: STREAM_TIMEOUT_MS,
  });
  const office = page.getByRole("region", { name: "Qayerga borish kerak" });
  await expect(office.getByText("NAMUNA Chilonzor tumani FHDYo boʻlimi")).toBeVisible();
  await expect(office.getByText("Tushlik tanaffusi · 14:00 da ochiladi")).toBeVisible();
});

test("J5 · stop → reload → retry keeps both attempts; limits; offline", async ({ page, context }) => {
  await logInSeedUser(page);
  await ask(page, "NAMUNA: Haydovchilik guvohnomasini qanday almashtiraman?");
  // Stop after `meta`, so the stopped message is stored and survives the reload.
  await expect(page).toHaveURL(/\/c\/[0-9a-f-]+$/);
  await page.getByRole("button", { name: "Toʻxtatish" }).click();
  await expect(page.getByText(/Javob toʻxtatildi\. Savolni qayta yuborishingiz mumkin\./)).toBeVisible();
  await expect(page.getByLabel("Savolingiz")).toBeFocused();

  await page.reload();
  await expect(page.getByText("Javob toʻxtatildi", { exact: true })).toBeVisible();
  await expectAccessible(page);
  await page.getByRole("button", { name: "Qayta urinish" }).click();
  await waitForFinal(page);
  await expect(page.locator("li.msg-user", { hasText: "NAMUNA: Haydovchilik guvohnomasini" })).toHaveCount(2);
  await expect(page.getByRole("button", { name: "Qayta urinish" })).toHaveCount(0);

  await ask(page, "NAMUNA: yana bir savol #limit");
  await expect(
    page.getByText("Bir soatda 20 tagacha savol berish mumkin. 21 daqiqadan soʻng yana soʻrang."),
  ).toBeVisible();
  await expect(page.getByLabel("Savolingiz")).toBeDisabled();

  await page.getByRole("link", { name: "Yangi suhbat" }).first().click();
  await ask(page, "Savol #quota");
  await expect(page.getByText("Bugungi savollar chegarasiga yetdingiz. Ertaga yana soʻrang.")).toBeVisible();
  await page.getByRole("link", { name: "Yangi suhbat" }).first().click();
  await ask(page, "Savol #globalquota");
  await expect(page.getByText(/xizmatning umumiy chegarasiga yetildi/)).toBeVisible();

  await context.setOffline(true);
  await expect(page.getByText(/Internet aloqasi yoʻq/)).toBeVisible();
  await expect(page.getByLabel("Savolingiz")).toBeDisabled();
  await context.setOffline(false);
  await expect(page.getByText("Aloqa tiklandi.")).toBeVisible();
});

test("J6 · history → delete → Russian UI → change password → log out → forgot → reset", async ({ page }) => {
  await logInSeedUser(page);
  await page.goto("/history");
  const main = page.getByRole("main");
  await expect(main.getByText("NAMUNA suhbat 3")).toBeVisible();
  await expectAccessible(page);
  await main.getByRole("link", { name: /Pasportni almashtirish/ }).click();
  await expect(page.getByRole("heading", { level: 2, name: "Pasportni almashtirish" })).toBeVisible();

  await page.goto("/history");
  await page.getByRole("main").getByRole("button", { name: "“NAMUNA suhbat 3” suhbatini oʻchirish" }).click();
  const dialog = page.getByRole("main").getByRole("alertdialog");
  await expect(dialog.getByRole("button", { name: "Bekor qilish" })).toBeFocused();
  await expectAccessible(page);
  await dialog.getByRole("button", { name: "Oʻchirish" }).click();
  await expect(page.getByText("Suhbat oʻchirildi")).toBeVisible();
  await expect(page.getByRole("main").getByText("NAMUNA suhbat 3")).toHaveCount(0);

  await page.goto("/settings");
  await page.getByRole("radio", { name: /Русский/ }).click();
  await expect(page.getByRole("radio", { name: /Русский/ })).toBeChecked();
  await expect(page.getByRole("heading", { level: 1, name: "Настройки" })).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("lang", "ru");
  await expectAccessible(page);
  await page.getByRole("button", { name: "Сменить пароль" }).click();
  await page.getByLabel("Текущий пароль").fill("namuna-parol-1");
  await page.getByLabel("Новый пароль", { exact: true }).fill("Yangi-parol-123");
  await page.getByRole("button", { name: "Сохранить пароль" }).click();
  await expect(page.getByText("Пароль изменён.")).toBeVisible();
  await page.getByRole("button", { name: "Выйти" }).click();
  await expect(page).toHaveURL(/\/welcome$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(/Какие документы, какое учреждение/);

  await clickLandingHeaderLink(page, "Войти", "Открыть меню");
  await page.getByRole("link", { name: "Забыли пароль?" }).click();
  await expect(page.getByRole("heading", { name: "Восстановление пароля" })).toBeVisible();
  await page.getByLabel("Электронная почта").fill("namuna@example.com");
  const resetPath = await emailedPath(page, () =>
    page.getByRole("button", { name: "Отправить ссылку" }).click(),
  );
  await expect(page.getByText(/мы отправили ссылку/)).toBeVisible();
  await page.goto(resetPath);
  await expect(page.getByRole("heading", { name: "Новый пароль" })).toBeVisible();
  await page.getByLabel("Новый пароль", { exact: true }).fill("Boshqa-parol-123");
  await page.getByRole("button", { name: "Сохранить пароль" }).click();
  await expect(page.getByText("Пароль обновлён. Войдите с новым паролем.")).toBeVisible();
  await page.getByRole("link", { name: "Войти" }).last().click();
  await expect(page.getByRole("heading", { name: "Вход в аккаунт" })).toBeVisible();
});

test("the phone drawer is modal: Tab stays in the sidebar, Esc returns focus to the menu", async ({
  page,
}) => {
  test.skip((page.viewportSize()?.width ?? 0) >= 1280, "the sidebar is persistent on desktop");
  await logInSeedUser(page);
  const menu = page.getByRole("button", { name: "Menyu", exact: true });
  await menu.click();
  await expect(page.getByRole("button", { name: "Yopish" })).toBeFocused();
  for (let step = 0; step < 15; step += 1) {
    await page.keyboard.press("Tab");
    const inSidebar = await page.evaluate(() => document.activeElement?.closest("#sidebar") !== null);
    const onPage = await page.evaluate(() => document.activeElement?.closest(".main-col") !== null);
    expect(onPage, `Tab ${String(step + 1)} reached the page behind the drawer`).toBe(false);
    if (!inSidebar) break;
  }
  await page.keyboard.press("Escape");
  await expect(menu).toBeFocused();
  await expectAccessible(page);
});
