import { describe, expect, it } from "vitest";
import { failureMessage, storedFailureMessage } from "./failureMessage";

/** Hourly limit shown in the rate-limit copy. */
const HOUR_LIMIT = 20;

/** Failures map to copy.md's error table (screen 12). */
describe("failureMessage", () => {
  it.each([
    [{ kind: "network" }, { key: "error.server", tone: "danger", retry: true }],
    [
      { kind: "stream", code: "llm_timeout", scope: null },
      { key: "chat_error.llm_timeout", tone: "danger", retry: true },
    ],
    [
      { kind: "stream", code: "internal_error", scope: null },
      { key: "error.server", tone: "danger", retry: true },
    ],
    [
      { kind: "stream", code: "stream_in_progress", scope: null },
      { key: "chat_error.stream_in_progress", tone: "warning", retry: true },
    ],
    [
      { kind: "stream", code: "quota_exceeded", scope: "global" },
      { key: "chat_error.quota_global", tone: "warning", retry: false, icon: "clock" },
    ],
    [
      { kind: "request", code: "quota_exceeded", retryAfter: 3600, scope: "user" },
      { key: "chat_error.quota_user", tone: "warning", retry: false, icon: "clock" },
    ],
    [
      { kind: "request", code: "rate_limited", retryAfter: 1260, scope: null },
      {
        key: "chat_error.rate_limited",
        values: { limit: 20, minutes: 21 },
        tone: "warning",
        retry: false,
        icon: "clock",
      },
    ],
    [
      { kind: "request", code: "validation_error", retryAfter: null, scope: null },
      { key: "error.server", tone: "danger", retry: true },
    ],
  ] as const)("%o", (failure, expected) => {
    expect(failureMessage(failure, HOUR_LIMIT)).toEqual({ titleKey: "chat_error.title", ...expected });
  });
});

/** Stored failed answers (`error_code`). */
describe("storedFailureMessage", () => {
  it("shows 'Answer stopped' with Retry", () => {
    expect(storedFailureMessage("stopped", HOUR_LIMIT)).toEqual({
      titleKey: "chat_error.stopped_title",
      key: "chat_error.stopped",
      tone: "warning",
      retry: true,
      icon: "square",
    });
  });

  it("uses the error copy for other codes and the server error when unknown", () => {
    expect(storedFailureMessage("llm_unavailable", HOUR_LIMIT).key).toBe("chat_error.llm_unavailable");
    expect(storedFailureMessage(null, HOUR_LIMIT).key).toBe("error.server");
  });
});
