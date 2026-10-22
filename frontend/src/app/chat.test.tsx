import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { delay, http, HttpResponse } from "msw";
import type { AssistantMessage } from "../api/types";
import { server } from "../mocks/server";
import { encodeFrame } from "../mocks/sse";
import { db } from "../mocks/db";
import { STALE_STREAMING_MS } from "../features/chat/streamingMessages";
import { renderApp, signInSeedUser } from "../test/render";

/**
 * A chat stream that sends `meta` and the start of an answer, then stays open (so Stop can be pressed).
 *
 * @returns The one-shot handler.
 */
function partialThenHang() {
  return http.post(
    "/api/v1/chat",
    () => {
      const frames = [
        encodeFrame({
          event: "meta",
          data: { conversation_id: "c-hang", user_message_id: "u", assistant_message_id: "a" },
        }),
        encodeFrame({
          event: "delta",
          data: {
            text: '{"answer_type":"service","language":"uz-Latn","title":"NAMUNA: qisman javob","summary":"NAMUNA"',
          },
        }),
      ].join("");
      return new HttpResponse(
        new ReadableStream({
          start(controller) {
            controller.enqueue(new TextEncoder().encode(frames));
          },
        }),
        { headers: { "Content-Type": "text/event-stream" } },
      );
    },
    { once: true },
  );
}

/** Seeded conversation (mocks/db.ts). */
const SEED_CONVERSATION = "c0000000-0000-4000-8000-000000000001";
/** A post-answer refetch that lands long after the test is done. */
const REFETCH_DELAY_MS = 10_000;

/**
 * Type a question into the composer and press Enter.
 *
 * @param user user-event instance.
 * @param text The question.
 */
async function ask(user: ReturnType<typeof userEvent.setup>, text: string): Promise<void> {
  const input = await screen.findByLabelText("Savolingiz");
  await user.type(input, text);
  await user.keyboard("{Enter}");
}

/** A whole mock stream plus the history refetch; slow CI runners with coverage need more than 1 s. */
const SETTLE_TIMEOUT_MS = 5000;

/**
 * Wait until the latest answer has settled: the stream closed and the stored copy replaced the live one
 * (nothing busy, the live turn's status regions are gone), so its chips no longer change under a click.
 */
async function waitForSettledAnswer(): Promise<void> {
  await waitFor(
    () => {
      const assistants = document.querySelectorAll("li.assistant");
      const latest = assistants[assistants.length - 1];
      expect((latest as HTMLElement).querySelector('[aria-busy="true"]')).toBeNull();
      expect(within(latest as HTMLElement).queryAllByRole("status")).toHaveLength(0);
    },
    { timeout: SETTLE_TIMEOUT_MS },
  );
}

/**
 * Wait until an answer is final (its feedback bar is shown).
 *
 * @param count How many answers should be final.
 */
async function waitForFinal(count = 1): Promise<void> {
  await waitFor(() => expect(screen.getAllByText("Javob foydali boʻldimi?")).toHaveLength(count));
}

/** Chat screens 7–12 on the seeded account. */
describe("chat", () => {
  beforeEach(signInSeedUser);

  it("asks a starter chip, moves to /c/:id and renders the service answer in schema order", async () => {
    const user = userEvent.setup();
    const { router } = renderApp("/");
    await screen.findByRole("heading", { level: 1, name: /Salom!/ });
    await user.click(await screen.findByRole("button", { name: "Pasportimni qanday yangilayman?" }));
    await waitFor(() => expect(router.state.location.pathname).toMatch(/^\/c\//));
    await waitForFinal();
    const headings = within(screen.getByRole("main"))
      .getAllByRole("heading")
      .map((heading) => heading.textContent);
    expect(headings.slice(1)).toEqual([
      "Pasportni almashtirish",
      "Nima qilish kerak",
      "Oʻzingiz bilan oling",
      "Toʻlov",
      "Muddat",
      "Qayerga borish kerak",
      "Manbalar",
      "Yana soʻrashingiz mumkin",
    ]);
    expect(screen.getAllByRole("link", { name: "1-manba" }).length).toBeGreaterThan(0);
    expect(
      screen.getByText("Bu umumiy maʼlumot, yuridik maslahat emas. Rasmiy manbani tekshiring."),
    ).toBeInTheDocument();
  });

  it("saves 👍 at once, and 👎 with an optional comment", async () => {
    const user = userEvent.setup();
    renderApp(`/c/${SEED_CONVERSATION}`);
    await user.click(await screen.findByRole("button", { name: "Ha, foydali" }));
    expect(await screen.findByText("Rahmat! Fikringiz saqlandi.")).toBeInTheDocument();
    /** The seeded assistant message. */
    const stored = () => db.conversations[SEED_CONVERSATION]?.messages[1] as AssistantMessage;
    expect(stored().feedback).toEqual({ rating: 1, comment: "" });

    const feedback = within(screen.getByRole("region", { name: "Javob foydali boʻldimi?" }));
    await user.click(feedback.getByRole("button", { name: "Yoʻq, foydali emas" }));
    await user.type(feedback.getByLabelText("Nima yetishmadi? (ixtiyoriy)"), "NAMUNA izoh");
    await user.click(feedback.getByRole("button", { name: "Yuborish" }));
    await waitFor(() => expect(stored().feedback).toEqual({ rating: -1, comment: "NAMUNA izoh" }));
  });

  it("continues the same thread from a follow-up chip", async () => {
    const user = userEvent.setup();
    renderApp(`/c/${SEED_CONVERSATION}`);
    await user.click(await screen.findByRole("button", { name: "Pasportni onlayn almashtirsa boʻladimi?" }));
    await waitForFinal(2);
    expect(
      screen.getByRole("heading", { name: "NAMUNA: Pasportni onlayn almashtirish" }),
    ).toBeInTheDocument();
  });

  it("keeps the finished answer when a follow-up is asked before the post-answer refetch", async () => {
    let conversationFetches = 0;
    server.use(
      // The first load goes through; every later conversation fetch (the post-answer refetch) is late.
      http.get("/api/v1/conversations/:id", async () => {
        conversationFetches += 1;
        if (conversationFetches > 1) await delay(REFETCH_DELAY_MS);
        return undefined;
      }),
    );
    const user = userEvent.setup();
    renderApp(`/c/${SEED_CONVERSATION}`);
    await screen.findByRole("heading", { name: "Pasportni almashtirish", level: 2 });
    await ask(user, "NAMUNA: Pasportni onlayn almashtirsa boʻladimi?");
    await waitForFinal(2);
    server.use(partialThenHang());
    await ask(user, "Yana savol");
    expect(await screen.findByRole("heading", { name: "NAMUNA: qisman javob" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "NAMUNA: Pasportni onlayn almashtirish" }),
    ).toBeInTheDocument();
    expect(conversationFetches).toBeGreaterThan(1);
  });

  it("renders a legal answer in the question's script with law points before the steps", async () => {
    const user = userEvent.setup();
    renderApp("/");
    await ask(user, "NAMUNA: Йиллик меҳнат таътили ҳақида қонунда нима дейилган?");
    await waitForFinal();
    expect(screen.getByText("Huquqiy savol")).toBeInTheDocument();
    const headings = screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent);
    expect(headings.indexOf("Qonunda nima deyilgan")).toBeLessThan(
      headings.indexOf("Nima qilishingiz mumkin"),
    );
    expect(screen.getAllByText("Qonun matni")).toHaveLength(2);
    expect(
      screen.getByRole("heading", { name: "NAMUNA: Йиллик меҳнат таътили" }).closest("li"),
    ).toHaveAttribute("lang", "uz-Cyrl");
  });

  it("shows the region fallback office with unknown hours and phone", async () => {
    const user = userEvent.setup();
    renderApp("/");
    await ask(user, "NAMUNA: Как зарегистрироваться по месту жительства?");
    await waitForFinal();
    expect(screen.getByText(/hududingizdagi boshqa idora koʻrsatildi/)).toBeInTheDocument();
    expect(screen.getByText("Ish vaqti nomaʼlum")).toBeInTheDocument();
    expect(screen.getByText("Telefon raqami nomaʼlum")).toBeInTheDocument();
    expect(screen.getByText("Manbalarda koʻrsatilmagan")).toBeInTheDocument();
  });

  it("offers topic chips on off-topic, then not-found", async () => {
    const user = userEvent.setup();
    renderApp("/");
    await ask(user, "NAMUNA: Ertaga ob-havo qanday boʻladi?");
    expect(await screen.findByText(/davlat xizmatlari va Oʻzbekiston qonunlari/)).toBeInTheDocument();
    await waitForSettledAnswer();
    await user.click(screen.getByRole("button", { name: "NAMUNA savol: tugʻilganlik haqida guvohnoma" }));
    await waitForSettledAnswer();
    expect(screen.getByRole("heading", { name: "NAMUNA: aniq javob topilmadi" })).toBeInTheDocument();
    expect(screen.getByText(/boshqa soʻzlar bilan/)).toBeInTheDocument();
  });

  it("stops a stream and keeps the partial cards for this view", async () => {
    server.use(partialThenHang());
    const user = userEvent.setup();
    renderApp("/");
    await ask(user, "NAMUNA: Haydovchilik guvohnomasini qanday almashtiraman?");
    expect(await screen.findByRole("heading", { name: "NAMUNA: qisman javob" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Toʻxtatish" }));
    expect(
      await screen.findByText(/Javob toʻxtatildi\. Savolni qayta yuborishingiz mumkin\./),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "NAMUNA: qisman javob" })).toBeInTheDocument();
    expect(screen.getByLabelText("Savolingiz")).toHaveFocus();
  });

  it("shows a stored stopped answer after reload and retries it", async () => {
    const answer = db.conversations[SEED_CONVERSATION]?.messages[1] as AssistantMessage;
    Object.assign(answer, { status: "failed", error_code: "stopped", answer: null });
    const user = userEvent.setup();
    renderApp(`/c/${SEED_CONVERSATION}`);
    expect(await screen.findByText("Javob toʻxtatildi")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Qayta urinish" }));
    await waitForFinal();
  });

  it("polls a stored answer that is still streaming until it completes", async () => {
    const answer = db.conversations[SEED_CONVERSATION]?.messages[1] as AssistantMessage;
    const complete = { ...answer };
    Object.assign(answer, { status: "streaming", answer: null, created_at: new Date().toISOString() });
    renderApp(`/c/${SEED_CONVERSATION}`);
    expect(await screen.findByText(/Javob yozilmoqda/)).toBeInTheDocument();
    Object.assign(answer, complete);
    expect(
      await screen.findByRole("heading", { name: "Pasportni almashtirish", level: 2 }, { timeout: 5000 }),
    ).toBeInTheDocument();
  });

  it("shows a streaming row older than the stream lock as stopped, with Retry", async () => {
    const answer = db.conversations[SEED_CONVERSATION]?.messages[1] as AssistantMessage;
    const longAgo = new Date(Date.now() - STALE_STREAMING_MS - 1000).toISOString();
    Object.assign(answer, { status: "streaming", answer: null, created_at: longAgo });
    const user = userEvent.setup();
    renderApp(`/c/${SEED_CONVERSATION}`);
    expect(await screen.findByText("Javob toʻxtatildi")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Qayta urinish" }));
    await waitForFinal();
  });

  it("shows the rate limit with the hourly limit and minutes, and blocks the composer", async () => {
    const user = userEvent.setup();
    renderApp("/");
    await ask(user, "Savol #limit");
    expect(
      await screen.findByText("Bir soatda 20 tagacha savol berish mumkin. 21 daqiqadan soʻng yana soʻrang."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Savolingiz")).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Qayta urinish" })).not.toBeInTheDocument();
  });

  it("uses the global-quota copy when scope is global", async () => {
    const user = userEvent.setup();
    renderApp("/");
    await ask(user, "Savol #globalquota");
    expect(await screen.findByText(/xizmatning umumiy chegarasiga yetildi/)).toBeInTheDocument();
  });

  it("shows a lost lock race (SSE error, no meta) as 'previous answer still writing'", async () => {
    const user = userEvent.setup();
    renderApp("/");
    await ask(user, "Savol #race");
    expect(await screen.findByText("Oldingi javob hali yozilmoqda. U tugashini kuting.")).toBeInTheDocument();
  });

  it("counts from 900 characters and blocks sending over 1000", async () => {
    renderApp("/");
    const input = await screen.findByLabelText("Savolingiz");
    fireEvent.change(input, { target: { value: "x".repeat(950) } });
    expect(screen.getByText("950 / 1000")).toBeInTheDocument();
    fireEvent.change(input, { target: { value: "x".repeat(1045) } });
    expect(screen.getByText("Savol juda uzun. 1000 belgigacha qisqartiring.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Yuborish" })).toBeDisabled();
    expect(input).toHaveAttribute("aria-invalid", "true");
  });

  it("disables the composer offline and shows the banner, then a back-online toast", async () => {
    renderApp("/");
    await screen.findByLabelText("Savolingiz");
    const onLine = vi.spyOn(navigator, "onLine", "get").mockReturnValue(false);
    act(() => void window.dispatchEvent(new Event("offline")));
    expect(screen.getByText(/Internet aloqasi yoʻq/)).toBeInTheDocument();
    expect(screen.getByLabelText("Savolingiz")).toBeDisabled();
    onLine.mockReturnValue(true);
    act(() => void window.dispatchEvent(new Event("online")));
    expect(await screen.findByText("Aloqa tiklandi.")).toBeInTheDocument();
    onLine.mockRestore();
  });

  it("says when a conversation does not exist", async () => {
    renderApp("/c/c0000000-0000-4000-8000-00000000dead");
    expect(await screen.findByText("Sahifa topilmadi")).toBeInTheDocument();
  });
});
