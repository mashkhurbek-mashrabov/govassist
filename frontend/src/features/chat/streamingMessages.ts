/**
 * Stored assistant messages still marked `streaming` (another tab, a reload mid-answer, or a row the backend
 * never closed). The chat polls them with backoff and, once they are older than the backend's stream lock,
 * shows them as stopped so Retry is offered.
 */
import type { AssistantMessage, Message } from "../../api/types";

/** After this, a `streaming` row is dead: the backend stream lock lives 120 s (`SET NX EX 120`), plus margin. */
export const STALE_STREAMING_MS = 150_000;
/** Shortest and longest wait between polls. */
const POLL_MIN_MS = 2_000;
const POLL_MAX_MS = 15_000;
/** The wait grows with the message's age: a quarter of it, within the bounds above. */
const POLL_AGE_DIVISOR = 4;

/**
 * Whether a message is a `streaming` assistant row.
 *
 * @param message Any stored message.
 * @returns `true` for an assistant message with status `streaming`.
 */
function isStreamingRow(message: Message): message is AssistantMessage {
  return message.role === "assistant" && message.status === "streaming";
}

/**
 * How old a message is at a given time.
 *
 * @param message The message.
 * @param at Epoch milliseconds.
 * @returns Age in milliseconds (0 when the clocks disagree).
 */
function ageAt(message: AssistantMessage, at: number): number {
  return Math.max(0, at - Date.parse(message.created_at));
}

/**
 * Whether a message is a `streaming` row older than {@link STALE_STREAMING_MS}.
 *
 * @param message Any stored message.
 * @param at Epoch milliseconds.
 * @returns `true` when the row can no longer finish.
 */
function isStale(message: Message, at: number): boolean {
  return isStreamingRow(message) && ageAt(message, at) > STALE_STREAMING_MS;
}

/**
 * Turn stale `streaming` rows into stopped failures, so they render as "Answer stopped" with Retry.
 *
 * @param messages Stored messages.
 * @param at When they were fetched (epoch ms; `dataUpdatedAt`, so rendering stays pure).
 * @returns The messages, with stale rows marked `failed` / `stopped` (the same array when none are).
 */
export function settleStaleStreaming(messages: Message[], at: number): Message[] {
  if (!messages.some((message) => isStale(message, at))) return messages;
  return messages.map((message) =>
    isStale(message, at) ? { ...message, status: "failed", error_code: "stopped" } : message,
  );
}

/**
 * How long to wait before refetching a conversation with a `streaming` row.
 *
 * @param messages Stored messages.
 * @param at Now (epoch ms).
 * @returns Milliseconds until the next poll (one lands just after the row turns stale), or `false` when
 *   nothing is streaming any more.
 */
export function streamingPollInterval(messages: Message[], at: number): number | false {
  const latest = messages.filter(isStreamingRow).at(-1);
  if (!latest) return false;
  const age = ageAt(latest, at);
  if (age > STALE_STREAMING_MS) return false;
  const backoff = Math.min(POLL_MAX_MS, Math.max(POLL_MIN_MS, age / POLL_AGE_DIVISOR));
  return Math.min(backoff, STALE_STREAMING_MS - age + 1);
}
