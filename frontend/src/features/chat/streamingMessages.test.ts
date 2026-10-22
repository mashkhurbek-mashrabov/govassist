import { describe, expect, it } from "vitest";
import type { Message } from "../../api/types";
import { sampleAssistantMessage } from "../../mocks/db";
import { settleStaleStreaming, STALE_STREAMING_MS, streamingPollInterval } from "./streamingMessages";

/** A fixed "now". */
const NOW = Date.parse("2026-10-22T10:00:00Z");

/**
 * A stored assistant row created `ageMs` before {@link NOW}.
 *
 * @param ageMs Age in milliseconds.
 * @param status Message status.
 * @returns The message.
 */
function row(ageMs: number, status: "streaming" | "complete" = "streaming"): Message {
  return { ...sampleAssistantMessage("a"), status, created_at: new Date(NOW - ageMs).toISOString() };
}

/** Stale `streaming` rows become stopped failures; fresh ones are left alone. */
describe("settleStaleStreaming", () => {
  it("marks rows older than the stream lock as stopped", () => {
    const [settled] = settleStaleStreaming([row(STALE_STREAMING_MS + 1)], NOW);
    expect(settled).toMatchObject({ status: "failed", error_code: "stopped" });
  });

  it("returns the same array when nothing is stale", () => {
    const messages = [row(1000), row(STALE_STREAMING_MS + 1, "complete")];
    expect(settleStaleStreaming(messages, NOW)).toBe(messages);
  });
});

/** Poll with backoff while a row streams; one poll lands right after it turns stale. */
describe("streamingPollInterval", () => {
  it("does not poll without a streaming row or once it is stale", () => {
    expect(streamingPollInterval([row(0, "complete")], NOW)).toBe(false);
    expect(streamingPollInterval([row(STALE_STREAMING_MS + 1)], NOW)).toBe(false);
  });

  it("backs off with age between 2 s and 15 s", () => {
    expect(streamingPollInterval([row(0)], NOW)).toBe(2_000);
    expect(streamingPollInterval([row(20_000)], NOW)).toBe(5_000);
    expect(streamingPollInterval([row(100_000)], NOW)).toBe(15_000);
  });

  it("wakes up just after the row turns stale", () => {
    expect(streamingPollInterval([row(STALE_STREAMING_MS - 3_000)], NOW)).toBe(3_001);
  });
});
