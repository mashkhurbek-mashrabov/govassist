import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { encodeFrame } from "../mocks/sse";
import { server } from "../mocks/server";
import { signInSeedUser } from "../test/render";
import { streamChat, toChatEvent } from "./chatStream";
import { ApiError } from "./http";
import type { ChatEvent } from "./types";

/**
 * Collect every event of a stream.
 *
 * @param text Question.
 * @returns The events in order.
 */
async function collect(text: string): Promise<ChatEvent[]> {
  const events: ChatEvent[] = [];
  for await (const event of streamChat({ conversation_id: null, text }, new AbortController().signal)) {
    events.push(event);
  }
  return events;
}

/** streamChat(): SSE parsing, event order, pre-stream errors. */
describe("streamChat", () => {
  beforeEach(signInSeedUser);

  it("yields contract events in order and drops pings", async () => {
    const events = await collect("Pasportimni qanday yangilayman?");
    const names = events.map((event) => event.event);
    expect(names.slice(0, 5)).toEqual(["meta", "status", "status", "office", "status"]);
    expect(names.slice(-2)).toEqual(["final", "done"]);
    const json = events.flatMap((event) => (event.event === "delta" ? [event.data.text] : [])).join("");
    expect(JSON.parse(json)).toMatchObject({ answer_type: "service", title: "Pasportni almashtirish" });
  });

  it("ends with an error event when generation fails", async () => {
    const events = await collect("Savol #error");
    expect(events.at(-1)).toEqual({
      event: "error",
      data: { code: "llm_unavailable", message: "SAMPLE: model unavailable" },
    });
  });

  it("throws ApiError for problems before the stream", async () => {
    const error = await collect("Savol #limit").catch((caught: unknown) => caught);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ code: "rate_limited", retryAfter: 1260 });
  });

  it("parses events split across network chunks and ignores unknown events", async () => {
    const wire = `${encodeFrame({ event: "meta", data: { conversation_id: "c", user_message_id: "u", assistant_message_id: "a" } })}event: future\ndata: {}\n\n${encodeFrame({ event: "done", data: {} })}`;
    server.use(
      http.post(
        "/api/v1/chat",
        () =>
          new HttpResponse(
            new ReadableStream({
              start(controller) {
                const bytes = new TextEncoder().encode(wire);
                controller.enqueue(bytes.slice(0, 17));
                controller.enqueue(bytes.slice(17));
                controller.close();
              },
            }),
            { headers: { "Content-Type": "text/event-stream" } },
          ),
      ),
    );
    expect((await collect("x")).map((event) => event.event)).toEqual(["meta", "done"]);
  });
});

/** toChatEvent(): name filtering. */
describe("toChatEvent", () => {
  it("returns null for unnamed or unknown events", () => {
    expect(toChatEvent(undefined, "{}")).toBeNull();
    expect(toChatEvent("future", "{}")).toBeNull();
    expect(toChatEvent("status", '{"stage":"found"}')).toEqual({ event: "status", data: { stage: "found" } });
  });
});
