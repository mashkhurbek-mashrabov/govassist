import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { db, GOOGLE_ONLY_EMAIL, SEED_EMAIL } from "../mocks/db";
import { server } from "../mocks/server";
import { renderApp, signInSeedUser } from "../test/render";

/** History, settings and about (screens 13–15). */
describe("account pages", () => {
  beforeEach(signInSeedUser);

  it("lists history with Today/Yesterday/date and deletes after confirmation with a toast", async () => {
    const user = userEvent.setup();
    renderApp("/history");
    const main = within(await screen.findByRole("main"));
    expect(await main.findByText("NAMUNA suhbat 3")).toBeInTheDocument();
    expect(main.getByText("Bugun")).toBeInTheDocument();
    expect(main.getByText("Kecha")).toBeInTheDocument();
    expect(main.getByText("18.10.2026")).toBeInTheDocument();
    expect(main.getByText(/\[PASSPORT\] kabi belgilar/)).toBeInTheDocument();

    await user.click(main.getByRole("button", { name: "“NAMUNA suhbat 3” suhbatini oʻchirish" }));
    const dialog = within(main.getByRole("alertdialog"));
    expect(dialog.getByRole("heading", { name: "Suhbat oʻchirilsinmi?" })).toBeInTheDocument();
    expect(dialog.getByRole("button", { name: "Bekor qilish" })).toHaveFocus();
    await user.click(dialog.getByRole("button", { name: "Oʻchirish" }));
    expect(await screen.findByText("Suhbat oʻchirildi")).toBeInTheDocument();
    await waitFor(() => expect(main.queryByText("NAMUNA suhbat 3")).not.toBeInTheDocument());
  });

  it("shows the empty history state", async () => {
    db.conversations = {};
    renderApp("/history");
    expect(await within(await screen.findByRole("main")).findByText("Hali suhbat yoʻq")).toBeInTheDocument();
  });

  it("switches the app language at once and localizes place names", async () => {
    const user = userEvent.setup();
    renderApp("/settings");
    await user.click(await screen.findByRole("radio", { name: /Русский/ }));
    expect(await screen.findByRole("heading", { name: "Настройки", level: 1 })).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("ru");
    expect(screen.getByRole("radio", { name: /Русский/ })).toBeChecked();
    await waitFor(() => expect(db.users[SEED_EMAIL]?.ui_language).toBe("ru"));
  });

  it("saves the area as region + district together", async () => {
    const user = userEvent.setup();
    renderApp("/settings");
    await user.click(await screen.findByRole("combobox", { name: "Viloyat" }));
    await user.click(await screen.findByRole("option", { name: "NAMUNA viloyati" }));
    expect(screen.getByRole("combobox", { name: "Tuman yoki shahar" })).toHaveValue("");
    await user.click(screen.getByRole("button", { name: "Saqlash" }));
    expect(await screen.findByText("Tuman yoki shaharni tanlang.")).toBeInTheDocument();
    await user.click(screen.getByRole("combobox", { name: "Tuman yoki shahar" }));
    await user.click(await screen.findByRole("option", { name: "NAMUNA-2 tumani" }));
    await user.click(screen.getByRole("button", { name: "Saqlash" }));
    expect(await screen.findByText("Saqlandi")).toBeInTheDocument();
    expect(db.users[SEED_EMAIL]?.district?.id).toBe(9000101);
  });

  it("filters the region list in either script", async () => {
    const user = userEvent.setup();
    renderApp("/settings");
    await user.type(await screen.findByRole("combobox", { name: "Viloyat" }), "Тош");
    expect(await screen.findByRole("option", { name: "Toshkent shahri" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "NAMUNA viloyati" })).not.toBeInTheDocument();
  });

  it("shows the hour and day usage meters", async () => {
    renderApp("/settings");
    expect(await screen.findByRole("meter", { name: "Shu soatda: 0 / 20 savol" })).toHaveAttribute(
      "aria-valuemax",
      "20",
    );
    expect(screen.getByRole("meter", { name: "Bugun: 0 / 100 savol" })).toBeInTheDocument();
  });

  it("changes the password: wrong current password, then success", async () => {
    const user = userEvent.setup();
    renderApp("/settings");
    await user.click(await screen.findByRole("button", { name: "Parolni oʻzgartirish" }));
    await user.type(screen.getByLabelText("Joriy parol"), "wrong-password");
    await user.type(screen.getByLabelText("Yangi parol"), "yangi-Parol-123");
    await user.click(screen.getByRole("button", { name: "Parolni saqlash" }));
    expect(await screen.findByText("Joriy parol notoʻgʻri.")).toBeInTheDocument();
    // Contract v1.8: `enter_current_password` is a field error on the current password.
    expect(screen.getByLabelText("Joriy parol")).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByLabelText("Joriy parol")).toHaveAccessibleDescription(/Joriy parol notoʻgʻri\./);
    await user.clear(screen.getByLabelText("Joriy parol"));
    await user.type(screen.getByLabelText("Joriy parol"), "eski-parol-123");
    await user.click(screen.getByRole("button", { name: "Parolni saqlash" }));
    expect(await screen.findByText("Parol oʻzgartirildi.")).toBeInTheDocument();
  });

  it("lets a Google-only account set a first password without the current one", async () => {
    db.sessionEmail = GOOGLE_ONLY_EMAIL;
    const user = userEvent.setup();
    renderApp("/settings");
    await user.click(await screen.findByRole("button", { name: "Parol oʻrnatish" }));
    expect(screen.getByText(/Hozir Google orqali kirasiz/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Joriy parol")).not.toBeInTheDocument();
    await user.type(screen.getByLabelText("Yangi parol"), "birinchi-Parol-1");
    await user.click(screen.getByRole("button", { name: "Parolni saqlash" }));
    expect(await screen.findByText("Parol oʻzgartirildi.")).toBeInTheDocument();
    expect(db.users[GOOGLE_ONLY_EMAIL]?.has_password).toBe(true);
    expect(screen.getByRole("button", { name: "Parolni oʻzgartirish" })).toBeInTheDocument();
  });

  it("logs out to the landing page", async () => {
    const user = userEvent.setup();
    const { router } = renderApp("/settings");
    await user.click(await screen.findByRole("button", { name: "Chiqish" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/welcome"));
    expect(db.sessionEmail).toBeNull();
  });

  it("deletes the account only after ticking 'I understand'", async () => {
    const user = userEvent.setup();
    const { router } = renderApp("/settings");
    await user.click(await screen.findByRole("button", { name: "Hisobni oʻchirish" }));
    const dialog = within(screen.getByRole("alertdialog"));
    const confirm = dialog.getByRole("button", { name: "Ha, oʻchirish" });
    expect(confirm).toBeDisabled();
    await user.click(dialog.getByRole("checkbox", { name: "Tushundim, hisobim oʻchirilsin" }));
    await user.click(confirm);
    await waitFor(() => expect(router.state.location.pathname).toBe("/welcome"));
    expect(db.users[SEED_EMAIL]).toBeUndefined();
  });

  it("saves the display name on blur", async () => {
    const user = userEvent.setup();
    renderApp("/settings");
    await user.type(await screen.findByLabelText("Ism (ixtiyoriy)"), "NAMUNA Ism");
    await user.tab();
    await waitFor(() => expect(db.users[SEED_EMAIL]?.display_name).toBe("NAMUNA Ism"));
  });

  it("opens and closes the history drawer from the top bar", async () => {
    const user = userEvent.setup();
    renderApp("/settings");
    const menu = await screen.findByRole("button", { name: "Menyu" });
    expect(menu).toHaveAttribute("aria-expanded", "false");
    await user.click(menu);
    expect(menu).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("button", { name: "Yopish" })).toHaveFocus();
    // Modal on phones: the top bar, page and composer behind the drawer are inert.
    expect(menu.closest(".main-col")).toHaveAttribute("inert");
    await user.keyboard("{Escape}");
    expect(menu).toHaveAttribute("aria-expanded", "false");
    expect(menu.closest(".main-col")).not.toHaveAttribute("inert");
    expect(menu).toHaveFocus();
  });
});

/** About and landing for everyone. */
describe("public pages", () => {
  it("lists sources on About and hides a missing fetch date", async () => {
    server.use(
      http.get("/api/v1/sources", () =>
        HttpResponse.json({
          items: [
            {
              publisher: "lex.uz",
              name: "NAMUNA Oila kodeksi",
              kind: "law",
              url: "https://lex.uz/",
              documents: 12,
              last_fetched_at: "2026-10-20T08:00:00Z",
            },
            {
              publisher: "lex.uz",
              name: "NAMUNA yangi manba",
              kind: "law",
              url: "https://lex.uz/new",
              documents: 3,
              last_fetched_at: null,
            },
          ],
        }),
      ),
    );
    renderApp("/about");
    expect(await screen.findByRole("link", { name: /NAMUNA Oila kodeksi/ })).toHaveAttribute(
      "rel",
      "noopener noreferrer",
    );
    expect(
      screen.getByText("lex.uz · Qonun hujjati · 12 ta hujjat · Yangilangan: 20.10.2026"),
    ).toBeInTheDocument();
    expect(screen.getByText("lex.uz · Qonun hujjati · 3 ta hujjat")).toBeInTheDocument();
  });

  it("keeps signed-in users away from /welcome", async () => {
    signInSeedUser();
    const { router } = renderApp("/welcome");
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
  });

  it("shows the 404 page", async () => {
    renderApp("/no-such-page");
    expect(await screen.findByRole("heading", { name: "Sahifa topilmadi" })).toBeInTheDocument();
  });
});
