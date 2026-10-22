import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { db, SEED_EMAIL, WRONG_PASSWORD } from "../mocks/db";
import { renderApp, signInSeedUser } from "../test/render";

/** Route guards and auth flows through the real route table and MSW. */
describe("auth flows", () => {
  it("sends anonymous visitors to /welcome, then through login back to the page", async () => {
    const user = userEvent.setup();
    const { router } = renderApp("/settings");
    await screen.findByRole("heading", { name: "Davlat xizmatlari va qonunlar — bosqichma-bosqich" });
    expect(router.state.location.pathname).toBe("/welcome");
    expect(router.state.location.search).toBe("?next=%2Fsettings");
    await user.click(screen.getByRole("link", { name: "Kirish" }));
    await screen.findByRole("heading", { name: "Kirish" });
    expect(router.state.location.search).toBe("?next=%2Fsettings");

    await user.click(screen.getByRole("button", { name: "Kirish" }));
    expect(await screen.findByText("Toʻgʻri elektron pochta manzilini kiriting.")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Elektron pochta"), SEED_EMAIL);
    await user.type(screen.getByLabelText("Parol"), WRONG_PASSWORD);
    await user.click(screen.getByRole("button", { name: "Kirish" }));
    expect(await screen.findByText("Elektron pochta yoki parol notoʻgʻri.")).toBeInTheDocument();

    await user.clear(screen.getByLabelText("Parol"));
    await user.type(screen.getByLabelText("Parol"), "namuna-parol-1");
    await user.click(screen.getByRole("button", { name: "Kirish" }));
    await screen.findByRole("heading", { name: "Sozlamalar", level: 1 });
  });

  it("signs up, verifies by link and lands in onboarding", async () => {
    const log = vi.spyOn(console, "info").mockImplementation(() => undefined);
    const user = userEvent.setup();
    const { router } = renderApp("/signup");
    await user.type(await screen.findByLabelText("Elektron pochta"), "yangi@example.com");
    await user.type(screen.getByLabelText("Parol"), "qisqa");
    await user.click(screen.getByRole("button", { name: "Roʻyxatdan oʻtish" }));
    expect(await screen.findByText("Kamida 10 ta belgidan foydalaning.")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Parol"), "-uzunroq-parol");
    await user.click(screen.getByRole("button", { name: "Roʻyxatdan oʻtish" }));
    await screen.findByRole("heading", { name: "Pochtangizni tekshiring" });

    const link = String(log.mock.calls.at(-1)?.[0]);
    await router.navigate(new URL(link.split(": ").at(-1) ?? "").pathname);
    await user.click(await screen.findByRole("button", { name: "Tasdiqlash" }));
    await screen.findByRole("heading", { name: "Qayerda yashaysiz?" });
    log.mockRestore();
  });

  it("rejects an invalid verification key", async () => {
    const user = userEvent.setup();
    renderApp("/verify-email/bad-key");
    await user.click(await screen.findByRole("button", { name: "Tasdiqlash" }));
    expect(await screen.findByText("Bu havola notoʻgʻri yoki muddati oʻtgan.")).toBeInTheDocument();
  });

  it("resets a password with the emailed key", async () => {
    const log = vi.spyOn(console, "info").mockImplementation(() => undefined);
    const user = userEvent.setup();
    const { router } = renderApp("/forgot-password");
    await user.type(await screen.findByLabelText("Elektron pochta"), SEED_EMAIL);
    await user.click(screen.getByRole("button", { name: "Havolani yuborish" }));
    await screen.findByText(/tiklash havolasi yuborildi/);

    await router.navigate(new URL(String(log.mock.calls.at(-1)?.[0]).split(": ").at(-1) ?? "").pathname);
    await user.type(await screen.findByLabelText("Yangi parol"), "yangi-parol-123");
    await user.type(screen.getByLabelText("Yangi parolni takrorlang"), "boshqa-parol-123");
    await user.click(screen.getByRole("button", { name: "Parolni saqlash" }));
    expect(await screen.findByText("Parollar mos kelmadi.")).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Yangi parolni takrorlang"));
    await user.type(screen.getByLabelText("Yangi parolni takrorlang"), "yangi-parol-123");
    await user.click(screen.getByRole("button", { name: "Parolni saqlash" }));
    expect(await screen.findByText("Parolingiz oʻzgartirildi. Iltimos, tizimga kiring.")).toBeInTheDocument();
    log.mockRestore();
  });

  it("keeps signed-in users away from guest pages and sends incomplete profiles to onboarding", async () => {
    signInSeedUser();
    const seed = db.users[SEED_EMAIL];
    if (seed) Object.assign(seed, { region: null, district: null, profile_complete: false });
    renderApp("/login");
    await screen.findByRole("heading", { name: "Qayerda yashaysiz?" });
  });
});

/** Onboarding, chat, history and settings on the seeded account. */
describe("signed-in app", () => {
  beforeEach(signInSeedUser);

  it("onboarding resets the district when the region changes and saves the profile", async () => {
    const seed = db.users[SEED_EMAIL];
    if (seed) Object.assign(seed, { region: null, district: null, profile_complete: false });
    const user = userEvent.setup();
    const { router } = renderApp("/onboarding");
    const region = await screen.findByLabelText("Viloyat");
    await screen.findByRole("option", { name: "Toshkent shahri" });
    await user.click(screen.getByRole("button", { name: "Davom etish" }));
    expect(await screen.findAllByText("Iltimos, tanlang.")).toHaveLength(2);

    await user.selectOptions(region, "Toshkent shahri");
    await user.selectOptions(await screen.findByLabelText("Tuman"), "Chilonzor tumani");
    await user.selectOptions(region, "NAMUNA viloyati");
    expect(screen.getByLabelText("Tuman")).toHaveValue("");
    await user.selectOptions(
      await screen.findByLabelText("Tuman"),
      await screen.findByRole("option", { name: "NAMUNA-2 tumani" }),
    );
    await user.click(screen.getByRole("button", { name: "Davom etish" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
    expect(db.users[SEED_EMAIL]?.district?.name).toBe("NAMUNA-2 tumani");
  });

  it("asks a starter question, moves to /c/:id and shows the streamed answer", async () => {
    const user = userEvent.setup();
    const { router } = renderApp("/");
    await user.click(
      await screen.findByRole("button", { name: "Tugʻilganlik haqidagi guvohnomani qanday olaman?" }),
    );
    await waitFor(() => expect(router.state.location.pathname).toMatch(/^\/c\//));
    // The live card is replaced by the stored copy once the conversation refetches, so never hold
    // element references across awaits: re-query the settled page in one waitFor.
    await waitFor(() => {
      expect(screen.getByText("Bu javob foydali boʻldimi?")).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Kerakli hujjatlar" })).toBeInTheDocument();
      expect(
        screen.getByText("Tugʻilganlik haqidagi guvohnomani qanday olaman?", { selector: "div" }),
      ).toBeInTheDocument();
    });
  });

  it("shows an existing conversation and a not-found conversation", async () => {
    const { router } = renderApp("/c/c0000000-0000-4000-8000-000000000001");
    expect(
      await screen.findByText("Pasportimni qanday yangilayman?", { selector: "div" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Pasportni almashtirish", level: 2 })).toBeInTheDocument();
    await router.navigate("/c/missing");
    expect(await screen.findByText("Bu suhbat mavjud emas yoki oʻchirilgan.")).toBeInTheDocument();
  });

  it("deletes a conversation from history after confirmation", async () => {
    const user = userEvent.setup();
    renderApp("/history");
    const main = within(await screen.findByRole("main"));
    await user.click(await main.findByRole("button", { name: "“Pasportni almashtirish” ni oʻchirish" }));
    const dialog = within(screen.getByRole("dialog"));
    await user.click(dialog.getByRole("button", { name: "Oʻchirish" }));
    expect(await main.findByText("Hali suhbatlar yoʻq.")).toBeInTheDocument();
  });

  it("changes the language from settings and logs out", async () => {
    const user = userEvent.setup();
    const { router } = renderApp("/settings");
    await user.selectOptions(await screen.findByLabelText("Til"), "Русский");
    await user.click(screen.getByRole("button", { name: "Saqlash" }));
    expect(await screen.findByRole("heading", { name: "Настройки", level: 1 })).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("ru");
    await user.click(screen.getByRole("button", { name: "Выйти" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    expect(db.sessionEmail).toBeNull();
  });

  it("deletes the account after confirmation", async () => {
    const user = userEvent.setup();
    const { router } = renderApp("/settings");
    await user.click(await screen.findByRole("button", { name: "Akkauntni oʻchirish" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Akkauntni oʻchirish" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    expect(db.users[SEED_EMAIL]).toBeUndefined();
  });
});
