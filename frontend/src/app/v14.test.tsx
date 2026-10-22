import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act, renderHook } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { getDistricts, listConversations, updateMe } from "../api/endpoints";
import { ApiError, CSRF_HEADER, request } from "../api/http";
import type { ConversationSummary } from "../api/types";
import { useChatStream } from "../features/chat/useChatStream";
import { conversationLabel } from "../features/history/conversationLabel";
import { db, SEED_EMAIL } from "../mocks/db";
import { server } from "../mocks/server";
import { queryWrapper, renderApp, signInSeedUser, testQueryClient } from "../test/render";

/**
 * A fresh handler that answers one chat POST with 409 stream_in_progress.
 *
 * @returns The one-shot handler.
 */
const busyOnce = () =>
  http.post(
    "/api/v1/chat",
    () =>
      HttpResponse.json(
        { type: "about:blank", title: "Conflict", status: 409, code: "stream_in_progress", errors: null },
        { status: 409, headers: { "Content-Type": "application/problem+json" } },
      ),
    { once: true },
  );

/** Contract v1.4 changes (from the frontend cross-check of backend PR #3). */
describe("contract v1.4", () => {
  beforeEach(signInSeedUser);

  it("refetches the CSRF cookie on csrf_failed and retries once", async () => {
    document.cookie = "csrftoken=stale";
    const sent: (string | null)[] = [];
    server.use(
      http.get("/api/v1/csrf", () => {
        document.cookie = "csrftoken=fresh";
        return new HttpResponse(null, { status: 204 });
      }),
      http.post("/x", ({ request: incoming }) => {
        const token = incoming.headers.get(CSRF_HEADER);
        sent.push(token);
        return token === "fresh"
          ? HttpResponse.json({ ok: true })
          : HttpResponse.json(
              { type: "about:blank", title: "Forbidden", status: 403, code: "csrf_failed", errors: null },
              { status: 403, headers: { "Content-Type": "application/problem+json" } },
            );
      }),
    );
    await expect(request("/x", { method: "POST", body: {} })).resolves.toEqual({ ok: true });
    expect(sent).toEqual(["stale", "fresh"]);
  });

  it("gives up after one CSRF retry", async () => {
    let csrfCalls = 0;
    server.use(
      http.get("/api/v1/csrf", () => {
        csrfCalls += 1;
        return new HttpResponse(null, { status: 204 });
      }),
      http.post("/x", () =>
        HttpResponse.json(
          { type: "about:blank", title: "Forbidden", status: 403, code: "csrf_failed", errors: null },
          { status: 403, headers: { "Content-Type": "application/problem+json" } },
        ),
      ),
    );
    const error = await request("/x", { method: "POST", body: {} }).catch((caught: unknown) => caught);
    expect(error).toMatchObject({ status: 403, code: "csrf_failed" });
    expect(csrfCalls).toBe(1);
  });

  it("does not retry permission_denied", async () => {
    let calls = 0;
    server.use(
      http.post("/x", () => {
        calls += 1;
        return HttpResponse.json(
          { type: "about:blank", title: "Forbidden", status: 403, code: "permission_denied", errors: null },
          { status: 403, headers: { "Content-Type": "application/problem+json" } },
        );
      }),
    );
    await expect(request("/x", { method: "POST", body: {} })).rejects.toBeInstanceOf(ApiError);
    expect(calls).toBe(1);
  });

  it("hides the About date when last_fetched_at is null", async () => {
    server.use(
      http.get("/api/v1/sources", () =>
        HttpResponse.json({
          items: [
            {
              publisher: "lex.uz",
              name: "NAMUNA yangi manba",
              kind: "law",
              url: "https://lex.uz/",
              documents: 3,
              last_fetched_at: null,
            },
          ],
        }),
      ),
    );
    renderApp("/about");
    await screen.findByRole("link", { name: "NAMUNA yangi manba" });
    expect(screen.getByText(/hujjatlar: 3$/)).toBeInTheDocument();
    expect(screen.queryByText(/1970/)).not.toBeInTheDocument();
  });

  it("names history items by title, else by the last question", () => {
    const item: ConversationSummary = { id: "c", title: "", updated_at: "", last_message_preview: "Savol" };
    expect(conversationLabel(item)).toBe("Savol");
    expect(conversationLabel({ ...item, title: "Sarlavha" })).toBe("Sarlavha");
  });

  it("shows not-found for a bad conversation id even without a problem body", async () => {
    server.use(
      http.get("/api/v1/conversations/:id", () => new HttpResponse("<h1>404</h1>", { status: 404 })),
    );
    renderApp("/c/not-a-uuid");
    expect(await screen.findByText("Bu suhbat mavjud emas yoki oʻchirilgan.")).toBeInTheDocument();
  });

  it("returns 404 not_found for an unknown region", async () => {
    await expect(getDistricts(424242, "uz-Latn")).rejects.toMatchObject({ status: 404, code: "not_found" });
  });

  it("previews the last user question (≤ 120 chars) and titles by question, then by answer", async () => {
    const question = `Savol #error ${"x".repeat(200)}`;
    const { result } = renderHook(() => useChatStream(), { wrapper: queryWrapper(testQueryClient()) });
    act(() => result.current.send(question, null));
    await waitFor(() => expect(result.current.turn?.isStreaming).toBe(false));
    const failed = (await listConversations(null)).results[0];
    expect(failed?.last_message_preview).toBe(question.slice(0, 120));
    expect(failed?.title).toBe(question.slice(0, 60));

    act(() => result.current.send("Pasportimni qanday yangilayman?", failed?.id ?? null));
    await waitFor(() => expect(result.current.turn?.finalMessage).not.toBeNull());
    const answered = (await listConversations(null)).results[0];
    expect(answered?.last_message_preview).toBe("Pasportimni qanday yangilayman?");
    expect(answered?.title).toBe("Pasportni almashtirish");
  });

  it("retries once after 409 stream_in_progress on Retry, not on a new question", async () => {
    const posts: string[] = [];
    server.events.on("request:start", ({ request: incoming }) => {
      if (incoming.url.endsWith("/chat")) posts.push(incoming.method);
    });
    const { result } = renderHook(() => useChatStream({ busyRetryDelayMs: 0 }), {
      wrapper: queryWrapper(testQueryClient()),
    });
    server.use(busyOnce());
    act(() => result.current.send("Savol", null));
    await waitFor(() =>
      expect(result.current.turn?.failure).toMatchObject({ kind: "request", code: "stream_in_progress" }),
    );
    expect(posts).toHaveLength(1);

    server.use(busyOnce());
    act(() => result.current.retry());
    await waitFor(() => expect(result.current.turn?.finalMessage).not.toBeNull());
    expect(result.current.turn?.failure).toBeNull();
    expect(posts).toHaveLength(3);
    server.events.removeAllListeners();
  });

  it("sends district_id whenever the region changes; region alone is rejected", async () => {
    const bodies: unknown[] = [];
    server.events.on("request:start", ({ request: incoming }) => {
      if (incoming.method === "PATCH")
        void incoming
          .clone()
          .json()
          .then((body) => bodies.push(body));
    });
    const user = userEvent.setup();
    renderApp("/settings");
    const region = await screen.findByLabelText("Viloyat");
    await screen.findByRole("option", { name: "NAMUNA viloyati" });
    await user.selectOptions(region, "NAMUNA viloyati");
    await user.selectOptions(
      screen.getByLabelText("Tuman"),
      await screen.findByRole("option", { name: "NAMUNA-2 tumani" }),
    );
    await user.click(screen.getByRole("button", { name: "Saqlash" }));
    await screen.findByText("Saqlandi.");
    expect(bodies).toEqual([{ ui_language: "uz-Latn", region_id: 90001, district_id: 9000101 }]);
    expect(db.users[SEED_EMAIL]?.district?.id).toBe(9000101);

    await expect(updateMe({ region_id: 1726 })).rejects.toMatchObject({
      status: 400,
      code: "validation_error",
      problem: { errors: { district_id: ["SAMPLE: required when the region changes"] } },
    });
    server.events.removeAllListeners();
  });
});
