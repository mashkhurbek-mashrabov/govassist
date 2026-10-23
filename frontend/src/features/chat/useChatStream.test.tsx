import { act, renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { sampleAssistantMessage } from "../../mocks/db";
import { SAMPLE_OFFICE } from "../../mocks/fixtures";
import { encodeFrame } from "../../mocks/sse";
import { server } from "../../mocks/server";
import { queryWrapper, signInSeedUser, testQueryClient } from "../../test/render";
import { parsePartialAnswer, turnReducer, useChatStream } from "./useChatStream";

/**
 * Mount the hook with a fresh query client.
 *
 * @param onConversationStarted Spy for new conversations.
 * @returns The hook result.
 */
function mountStream(onConversationStarted = vi.fn()) {
  return renderHook(() => useChatStream({ onConversationStarted }), {
    wrapper: queryWrapper(testQueryClient()),
  });
}

/** A stream that sends `meta` and then stays open until aborted. */
function hangingStream() {
  return http.post("/api/v1/chat", () => {
    const meta = { conversation_id: "c-hang", user_message_id: "u", assistant_message_id: "a" };
    return new HttpResponse(
      new ReadableStream({
        start(controller) {
          controller.enqueue(new TextEncoder().encode(encodeFrame({ event: "meta", data: meta })));
        },
      }),
      { headers: { "Content-Type": "text/event-stream" } },
    );
  });
}

/** useChatStream(): the full lifecycle against the mock SSE stream. */
describe("useChatStream", () => {
  beforeEach(signInSeedUser);

  it("streams a new chat to the final answer and reports the new conversation", async () => {
    const onStarted = vi.fn();
    const { result } = mountStream(onStarted);
    act(() => result.current.send("Pasportimni qanday yangilayman?", null));
    expect(result.current.turn?.isStreaming).toBe(true);
    await waitFor(() => expect(result.current.turn?.isStreaming).toBe(false));
    const turn = result.current.turn;
    expect(onStarted).toHaveBeenCalledWith(turn?.conversationId);
    expect(turn?.failure).toBeNull();
    expect(turn?.stage).toBe("writing");
    expect(turn?.sourceCount).toBe(2);
    expect(turn?.office?.match).toBe("district");
    expect(turn?.finalMessage?.answer?.title).toBe("Pasportni almashtirish");
  });

  it("ends a refused answer without an office (contract v1.7)", async () => {
    const { result } = mountStream();
    act(() => result.current.send("NAMUNA: idora oldida ob-havo qanday?", null));
    await waitFor(() => expect(result.current.turn?.isStreaming).toBe(false));
    expect(result.current.turn?.finalMessage?.answer?.answer_type).toBe("off_topic");
    expect(result.current.turn?.office).toBeNull();
  });

  it("renders a final-only stream (meta → final → done) for a sources answer (contract v1.11)", async () => {
    const { result } = mountStream();
    act(() => result.current.send("List the sources", "c0000000-0000-4000-8000-000000000001"));
    await waitFor(() => expect(result.current.turn?.isStreaming).toBe(false));
    const turn = result.current.turn;
    expect(turn?.failure).toBeNull();
    expect(turn?.partialAnswer).toBeNull();
    expect(turn?.finalMessage?.answer?.answer_type).toBe("sources");
    expect(turn?.finalMessage?.sources.map((source) => source.id)).toEqual(["S1", "S2"]);
    expect(turn?.office).toBeNull();
  });

  it("does not report a new conversation when continuing one", async () => {
    const onStarted = vi.fn();
    const { result } = mountStream(onStarted);
    act(() => result.current.send("Yana savol", "c0000000-0000-4000-8000-000000000001"));
    await waitFor(() => expect(result.current.turn?.finalMessage).not.toBeNull());
    expect(onStarted).not.toHaveBeenCalled();
  });

  it("shows an in-stream error and retries the same text", async () => {
    const requests: string[] = [];
    server.events.on("request:start", ({ request }) => {
      if (request.url.endsWith("/chat")) requests.push(request.method);
    });
    const { result } = mountStream();
    act(() => result.current.send("Savol #error", null));
    await waitFor(() =>
      expect(result.current.turn?.failure).toEqual({ kind: "stream", code: "llm_unavailable", scope: null }),
    );
    act(() => result.current.retry());
    await waitFor(() => expect(requests).toHaveLength(2));
    await waitFor(() => expect(result.current.turn?.isStreaming).toBe(false));
    expect(result.current.turn?.text).toBe("Savol #error");
    server.events.removeAllListeners();
  });

  it("reports pre-stream problems with retry_after", async () => {
    const { result } = mountStream();
    act(() => result.current.send("Savol #limit", null));
    await waitFor(() =>
      expect(result.current.turn?.failure).toEqual({
        kind: "request",
        code: "rate_limited",
        retryAfter: 1260,
        scope: null,
      }),
    );
  });

  it("stops a running stream", async () => {
    server.use(hangingStream());
    const { result } = mountStream();
    act(() => result.current.send("Savol", null));
    await waitFor(() => expect(result.current.turn?.conversationId).toBe("c-hang"));
    act(() => result.current.stop());
    await waitFor(() => expect(result.current.turn?.failure).toEqual({ kind: "stopped" }));
    expect(result.current.turn?.isStreaming).toBe(false);
  });

  it("ignores a second send while streaming and forgets the turn on reset", () => {
    server.use(hangingStream());
    const { result } = mountStream();
    act(() => result.current.send("Birinchi", null));
    act(() => result.current.send("Ikkinchi", null));
    expect(result.current.turn?.text).toBe("Birinchi");
    act(() => result.current.reset());
    expect(result.current.turn).toBeNull();
  });
});

/** turnReducer(): transitions not covered by a live stream. */
describe("turnReducer", () => {
  it("marks a stream that ended without final as a network failure", () => {
    const started = turnReducer(null, { type: "start", text: "Q", conversationId: null });
    expect(turnReducer(started, { type: "end" })).toMatchObject({
      isStreaming: false,
      failure: { kind: "network" },
    });
  });

  it("withdraws the early office when final has none (contract v1.7)", () => {
    const started = turnReducer(null, { type: "start", text: "Q", conversationId: null });
    const withOffice = turnReducer(started, { type: "office", office: SAMPLE_OFFICE });
    expect(withOffice?.office).toBe(SAMPLE_OFFICE);
    const message = { ...sampleAssistantMessage("a"), office: null };
    expect(turnReducer(withOffice, { type: "final", message })?.office).toBeNull();
  });

  it("ignores events when idle", () => {
    expect(turnReducer(null, { type: "end" })).toBeNull();
  });
});

/** parsePartialAnswer(): incomplete JSON fragments. */
describe("parsePartialAnswer", () => {
  it("reads cut-off strings and arrays", () => {
    expect(parsePartialAnswer('{"answer_type":"service","title":"Pasportni alm')).toEqual({
      answer_type: "service",
      title: "Pasportni alm",
    });
    expect(parsePartialAnswer('{"steps":[{"text":"Ariza')).toEqual({ steps: [{ text: "Ariza" }] });
  });

  it("returns null until something parses", () => {
    expect(parsePartialAnswer("")).toBeNull();
    expect(parsePartialAnswer('"just a string"')).toBeNull();
  });
});
