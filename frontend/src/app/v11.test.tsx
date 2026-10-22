import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { AssistantMessage } from "../api/types";
import { db, GOOGLE_ONLY_EMAIL, newUser, SEED_EMAIL } from "../mocks/db";
import { renderApp, signInSeedUser } from "../test/render";

/** Seeded conversation id (mocks/db.ts). */
const SEED_CONVERSATION = "c0000000-0000-4000-8000-000000000001";

/** Contract v1.1 / plan §3 and §6 additions. */
describe("contract v1.1 features", () => {
  it("resends the verification link from check-email and shows the wait on 429", async () => {
    vi.spyOn(console, "info").mockImplementation(() => undefined);
    const user = userEvent.setup();
    renderApp("/signup");
    await user.type(await screen.findByLabelText("Elektron pochta"), "qayta@example.com");
    await user.type(screen.getByLabelText("Parol"), "uzun-parol-123");
    await user.click(screen.getByRole("button", { name: "Roʻyxatdan oʻtish" }));
    await screen.findByRole("heading", { name: "Pochtangizni tekshiring" });
    expect(screen.getByLabelText("Elektron pochta")).toHaveValue("qayta@example.com");

    await user.click(screen.getByRole("button", { name: "Havolani qayta yuborish" }));
    expect(await screen.findByText(/yangi havola yuborildi/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Havolani qayta yuborish" }));
    expect(await screen.findByText("Yangi havola soʻrashdan oldin 1 daqiqa kuting.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Boshqa pochtadan foydalanish" })).toHaveAttribute(
      "href",
      "/signup",
    );
    vi.restoreAllMocks();
  });

  it("shows a stored stopped answer after reload and retries its question", async () => {
    signInSeedUser();
    const conversation = db.conversations[SEED_CONVERSATION];
    const answer = conversation?.messages[1] as AssistantMessage;
    Object.assign(answer, { status: "failed", error_code: "stopped", answer: null });
    const user = userEvent.setup();
    renderApp(`/c/${SEED_CONVERSATION}`);
    expect(await screen.findByText("Javob toʻxtatildi.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Qayta urinish" }));
    await waitFor(() => expect(screen.getByText("Bu javob foydali boʻldimi?")).toBeInTheDocument());
    expect(conversation?.messages.at(-2)).toMatchObject({
      role: "user",
      text: "Pasportimni qanday yangilayman?",
    });
  });

  it("uses the global-quota copy when scope is global", async () => {
    signInSeedUser();
    const user = userEvent.setup();
    renderApp("/");
    await user.type(await screen.findByLabelText("Savolingiz"), "Savol #globalquota{Enter}");
    expect(
      await screen.findByText("Xizmat kunlik chegarasiga yetdi. Ertaga qayta urinib koʻring."),
    ).toBeInTheDocument();
  });

  it("lets a Google-only account set a first password without the current one", async () => {
    db.sessionEmail = GOOGLE_ONLY_EMAIL;
    const user = userEvent.setup();
    renderApp("/settings");
    const section = within(
      (await screen.findByRole("heading", { name: "Parol oʻrnatish" })).closest("section") ?? document.body,
    );
    expect(section.queryByLabelText("Joriy parol")).not.toBeInTheDocument();
    await user.type(section.getByLabelText("Yangi parol"), "birinchi-parol-1");
    await user.click(section.getByRole("button", { name: "Parol oʻrnatish" }));
    expect(await screen.findByRole("heading", { name: "Parolni oʻzgartirish" })).toBeInTheDocument();
    expect(db.users[GOOGLE_ONLY_EMAIL]?.has_password).toBe(true);
    expect(screen.getByLabelText("Joriy parol")).toBeInTheDocument();
  });

  it("asks for the current password when the account has one", async () => {
    signInSeedUser();
    const user = userEvent.setup();
    renderApp("/settings");
    await user.type(await screen.findByLabelText("Yangi parol"), "yangi-parol-123");
    await user.click(screen.getByRole("button", { name: "Parolni oʻzgartirish" }));
    expect(await screen.findByText("Bu maydonni toʻldiring.")).toBeInTheDocument();
    expect(db.users[SEED_EMAIL]?.has_password).toBe(true);
  });

  it("lists the reviewed sources on the public About page", async () => {
    renderApp("/about");
    expect(await screen.findByRole("link", { name: "NAMUNA Oila kodeksi" })).toHaveAttribute(
      "rel",
      "noopener noreferrer",
    );
    expect(screen.getByText(/hujjatlar: 12 · 20\.10\.2026 da yangilangan/)).toBeInTheDocument();
  });

  it("keeps signed-in users away from /welcome", async () => {
    signInSeedUser();
    const { router } = renderApp("/welcome");
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
  });
});

/** Contract v1.3: enumeration-safe signup and URL-encoded keys in email links. */
describe("contract v1.3 auth changes", () => {
  it("answers signup with an existing email like a new signup", async () => {
    const log = vi.spyOn(console, "info").mockImplementation(() => undefined);
    const user = userEvent.setup();
    renderApp("/signup");
    await user.type(await screen.findByLabelText("Elektron pochta"), SEED_EMAIL);
    await user.type(screen.getByLabelText("Parol"), "uzun-parol-123");
    await user.click(screen.getByRole("button", { name: "Roʻyxatdan oʻtish" }));
    await screen.findByRole("heading", { name: "Pochtangizni tekshiring" });
    expect(String(log.mock.calls.at(-1)?.[0])).toContain("/forgot-password");
    vi.restoreAllMocks();
  });

  it("POSTs the decoded verification key from an encoded link", async () => {
    db.users["kalit@example.com"] = newUser("kalit@example.com", false);
    db.verificationKeys["MQ:abc/1"] = "kalit@example.com";
    const user = userEvent.setup();
    renderApp("/verify-email/MQ%3Aabc%2F1");
    await user.click(await screen.findByRole("button", { name: "Tasdiqlash" }));
    await screen.findByRole("heading", { name: "Qayerda yashaysiz?" });
    expect(db.users["kalit@example.com"].email_verified).toBe(true);
  });

  it("POSTs the decoded reset key from an encoded link", async () => {
    db.resetKeys["MQ:xyz"] = SEED_EMAIL;
    const user = userEvent.setup();
    renderApp("/reset-password/MQ%3Axyz");
    await user.type(await screen.findByLabelText("Yangi parol"), "yangi-parol-123");
    await user.type(screen.getByLabelText("Yangi parolni takrorlang"), "yangi-parol-123");
    await user.click(screen.getByRole("button", { name: "Parolni saqlash" }));
    await screen.findByText("Parolingiz oʻzgartirildi. Iltimos, tizimga kiring.");
    expect(db.resetKeys["MQ:xyz"]).toBeUndefined();
  });
});
