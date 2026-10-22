import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { db, newUser, SEED_EMAIL, WRONG_PASSWORD } from "../mocks/db";
import { server } from "../mocks/server";
import { renderApp, signInSeedUser } from "../test/render";

/**
 * Path of the last "[MSW mail]" link printed by the mock.
 *
 * @param log The console.info spy.
 * @returns The SPA path.
 */
function mailedPath(log: { mock: { calls: unknown[][] } }): string {
  return new URL(String(log.mock.calls.at(-1)?.[0]).split(": ").at(-1) ?? "").pathname;
}

/** Screens 0–6 through the real route table and MSW. */
describe("auth flows", () => {
  it("lands anonymous visitors on /welcome and keeps next through login", async () => {
    const user = userEvent.setup();
    const { router } = renderApp("/settings");
    await screen.findByRole("heading", { level: 1, name: /Davlat xizmatini qanday olishni/ });
    expect(router.state.location.pathname).toBe("/welcome");
    expect(router.state.location.search).toBe("?next=%2Fsettings");

    await user.click(within(screen.getByRole("main")).getByRole("link", { name: "Kirish" }));
    await screen.findByRole("heading", { name: "Hisobingizga kiring" });
    expect(router.state.location.search).toBe("?next=%2Fsettings");

    await user.click(screen.getByRole("button", { name: "Kirish" }));
    expect(await screen.findByText("Formada xatolar bor. Quyida tuzating.")).toBeInTheDocument();
    expect(
      screen.getByText("Toʻgʻri elektron pochta kiriting, masalan siz@example.com."),
    ).toBeInTheDocument();

    await user.type(screen.getByLabelText("Elektron pochta"), SEED_EMAIL);
    await user.type(screen.getByLabelText("Parol"), WRONG_PASSWORD);
    await user.click(screen.getByRole("button", { name: "Kirish" }));
    expect(await screen.findByText("Elektron pochta yoki parol notoʻgʻri.")).toBeInTheDocument();

    await user.clear(screen.getByLabelText("Parol"));
    await user.type(screen.getByLabelText("Parol"), "namuna-parol-1");
    await user.click(screen.getByRole("button", { name: "Kirish" }));
    await screen.findByRole("heading", { name: "Sozlamalar", level: 1 });
  });

  it("shows the rate-limit warning for allauth's bare 429 (contract v1.8)", async () => {
    const user = userEvent.setup();
    renderApp("/login");
    await user.type(await screen.findByLabelText("Elektron pochta"), "ratelimit@example.com");
    await user.type(screen.getByLabelText("Parol"), "namuna-parol-1");
    await user.click(screen.getByRole("button", { name: "Kirish" }));
    expect(
      await screen.findByText("Juda koʻp urinish boʻldi. Birozdan soʻng qayta urinib koʻring."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Nimadir xato ketdi. Birozdan soʻng qayta urinib koʻring.")).toBeNull();
  });

  it("toggles password visibility", async () => {
    const user = userEvent.setup();
    renderApp("/login");
    const input = await screen.findByLabelText("Parol");
    expect(input).toHaveAttribute("type", "password");
    await user.click(screen.getByRole("button", { name: "Parolni koʻrsatish" }));
    expect(input).toHaveAttribute("type", "text");
    expect(screen.getByRole("button", { name: "Parolni yashirish" })).toHaveAttribute("aria-pressed", "true");
  });

  it("signs up with a strength hint, verifies on load and continues to onboarding", async () => {
    const log = vi.spyOn(console, "info").mockImplementation(() => undefined);
    const user = userEvent.setup();
    const { router } = renderApp("/signup");
    await user.type(await screen.findByLabelText("Elektron pochta"), "yangi@example.com");
    await user.type(screen.getByLabelText("Parol"), "qisqa");
    expect(screen.getByText("kuchsiz")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Hisob yaratish" }));
    expect(await screen.findByText("Parol kamida 10 ta belgidan iborat boʻlsin.")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Parol"), "-Uzunroq-12");
    expect(screen.getByText("kuchli")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Hisob yaratish" }));
    await screen.findByRole("heading", { name: "Pochtangizni tekshiring" });
    expect(screen.getByText("yangi@example.com")).toBeInTheDocument();

    await router.navigate(mailedPath(log));
    await screen.findByRole("heading", { name: "Elektron pochta tasdiqlandi" });
    await user.click(screen.getByRole("button", { name: "Davom etish" }));
    await screen.findByRole("heading", { name: "Qaysi tilda gaplashamiz?" });
    log.mockRestore();
  });

  it("offers a new link for an invalid verification key", async () => {
    const user = userEvent.setup();
    const { router } = renderApp("/verify-email/bad-key");
    await screen.findByRole("heading", { name: "Havola yaroqsiz yoki muddati oʻtgan" });
    db.users["eski@example.com"] = newUser("eski@example.com", false);
    await user.type(screen.getByLabelText("Elektron pochta"), "eski@example.com");
    vi.spyOn(console, "info").mockImplementation(() => undefined);
    await user.click(screen.getByRole("button", { name: "Yangi havola yuborish" }));
    await screen.findByRole("heading", { name: "Pochtangizni tekshiring" });
    expect(router.state.location.pathname).toBe("/check-email");
    expect(screen.getByText("Havola qayta yuborildi.")).toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it("resets a password with the emailed (URL-encoded) key", async () => {
    const log = vi.spyOn(console, "info").mockImplementation(() => undefined);
    const user = userEvent.setup();
    const { router } = renderApp("/forgot-password");
    await user.type(await screen.findByLabelText("Elektron pochta"), SEED_EMAIL);
    await user.click(screen.getByRole("button", { name: "Havolani yuborish" }));
    await screen.findByText(/havola yubordik/);

    await router.navigate(mailedPath(log));
    await user.type(await screen.findByLabelText("Yangi parol"), "yangi-Parol-123");
    await user.click(screen.getByRole("button", { name: "Parolni saqlash" }));
    expect(await screen.findByText("Parol yangilandi. Endi yangi parol bilan kiring.")).toBeInTheDocument();
    log.mockRestore();
  });

  it("explains an invalid reset key", async () => {
    const user = userEvent.setup();
    renderApp("/reset-password/MQ%3Anope");
    await user.type(await screen.findByLabelText("Yangi parol"), "yangi-Parol-123");
    await user.click(screen.getByRole("button", { name: "Parolni saqlash" }));
    expect(
      await screen.findByText("Bu havola yaroqsiz yoki muddati oʻtgan. Yangisini soʻrang."),
    ).toBeInTheDocument();
  });

  it("onboards in two steps: language, then region and district", async () => {
    signInSeedUser();
    const seed = db.users[SEED_EMAIL];
    if (seed) Object.assign(seed, { region: null, district: null, profile_complete: false });
    const user = userEvent.setup();
    const { router } = renderApp("/login");
    await screen.findByRole("heading", { name: "Qaysi tilda gaplashamiz?" });
    expect(screen.getByText("1-qadam, jami 2")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Keyingi" }));

    await screen.findByRole("heading", { name: "Qayerda yashaysiz?" });
    expect(screen.getByRole("combobox", { name: "Tuman yoki shahar" })).toBeDisabled();
    expect(screen.getByText("Avval viloyatni tanlang")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Saqlash va boshlash" }));
    expect(await screen.findByText("Viloyatni tanlang.")).toBeInTheDocument();

    await user.click(screen.getByRole("combobox", { name: "Viloyat" }));
    await user.click(await screen.findByRole("option", { name: "Toshkent shahri" }));
    await user.click(screen.getByRole("combobox", { name: "Tuman yoki shahar" }));
    await user.click(await screen.findByRole("option", { name: "Chilonzor tumani" }));
    await user.click(screen.getByRole("button", { name: "Saqlash va boshlash" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
    expect(db.users[SEED_EMAIL]?.district?.id).toBe(1726269);
  });

  it("puts a server validation_error on its field, not in a silent or generic alert", async () => {
    signInSeedUser();
    const seed = db.users[SEED_EMAIL];
    if (seed) Object.assign(seed, { region: null, district: null, profile_complete: false });
    server.use(
      http.patch(
        "/api/v1/me",
        () =>
          HttpResponse.json(
            {
              type: "about:blank",
              title: "validation_error",
              status: 400,
              code: "validation_error",
              errors: { district_id: ["SAMPLE: district does not belong to region"] },
            },
            { status: 400, headers: { "Content-Type": "application/problem+json" } },
          ),
        { once: true },
      ),
    );
    const user = userEvent.setup();
    renderApp("/onboarding");
    await user.click(await screen.findByRole("button", { name: "Keyingi" }));
    await user.click(await screen.findByRole("combobox", { name: "Viloyat" }));
    await user.click(await screen.findByRole("option", { name: "Toshkent shahri" }));
    await user.click(screen.getByRole("combobox", { name: "Tuman yoki shahar" }));
    await user.click(await screen.findByRole("option", { name: "Chilonzor tumani" }));
    await user.click(screen.getByRole("button", { name: "Saqlash va boshlash" }));

    expect(await screen.findByText("Tuman yoki shaharni tanlang.")).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Tuman yoki shahar" })).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    expect(screen.queryByText("Nimadir xato ketdi. Birozdan soʻng qayta urinib koʻring.")).toBeNull();
    expect(screen.queryByText(/SAMPLE: district/)).toBeNull();
  });

  it("shows the session-ended notice after a 401", async () => {
    renderApp("/login?session=ended");
    expect(await screen.findByText("Sessiya tugadi. Qaytadan kiring.")).toBeInTheDocument();
  });
});
