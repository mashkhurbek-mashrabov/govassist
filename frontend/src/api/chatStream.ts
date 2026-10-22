/** `POST /api/v1/chat` as a typed async iterator of SSE events (contract §4). */
import { EventSourceParserStream } from "eventsource-parser/stream";
import { API_BASE } from "./endpoints";
import { ensureOk, send } from "./http";
import type { ChatEvent, ChatEventName, ChatRequest } from "./types";

/** Event names the SPA understands; anything else is ignored for forward compatibility. */
const KNOWN_EVENTS = new Set<string>([
  "meta",
  "status",
  "office",
  "delta",
  "final",
  "error",
  "done",
] satisfies ChatEventName[]);

/**
 * Narrow a parsed SSE message to a known chat event.
 *
 * @param name SSE `event:` field.
 * @param data SSE `data:` field (JSON text).
 * @returns The typed event, or `null` for unknown event names.
 */
export function toChatEvent(name: string | undefined, data: string): ChatEvent | null {
  if (name === undefined || !KNOWN_EVENTS.has(name)) return null;
  return { event: name, data: JSON.parse(data) as unknown } as ChatEvent;
}

/**
 * Send a question and yield the answer stream event by event. Comment pings are dropped by the parser.
 *
 * @param body Conversation id (or `null` for a new chat) and the question text.
 * @param signal Aborts the request (the Stop button).
 * @yields Typed chat events in wire order.
 * @throws {ApiError} When the server rejects the request before the stream starts.
 */
export async function* streamChat(body: ChatRequest, signal: AbortSignal): AsyncGenerator<ChatEvent> {
  const response = await ensureOk(
    await send(`${API_BASE}/chat`, {
      method: "POST",
      body,
      headers: { Accept: "text/event-stream" },
      signal,
    }),
  );
  if (!response.body) throw new Error("Chat response has no body");
  const reader = response.body
    .pipeThrough(new TextDecoderStream())
    .pipeThrough(new EventSourceParserStream())
    .getReader();
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) return;
      const event = toChatEvent(value.event, value.data);
      if (event) yield event;
    }
  } finally {
    reader.releaseLock();
  }
}
