/** When a limit blocks the composer (screen 12: "input disabled until then"). */
import type { LiveTurn } from "./useChatStream";

/** Milliseconds per second. */
const MS_PER_S = 1000;

/**
 * Epoch ms until which asking is blocked by a rate or quota limit with `retry_after`.
 *
 * @param turn The live turn.
 * @returns The end of the block, or `null` when nothing blocks.
 */
export function blockedUntil(turn: LiveTurn | null): number | null {
  const failure = turn?.failure;
  if (failure?.kind !== "request" || failure.retryAfter === null || turn?.failedAt == null) return null;
  if (failure.code !== "rate_limited" && failure.code !== "quota_exceeded") return null;
  return turn.failedAt + failure.retryAfter * MS_PER_S;
}
