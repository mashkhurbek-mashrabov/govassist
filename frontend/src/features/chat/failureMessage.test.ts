import { describe, expect, it } from "vitest";
import { failureMessage, storedFailureMessage } from "./failureMessage";

/** Every failure kind maps to an existing message key. */
describe("failureMessage", () => {
  it.each([
    [{ kind: "stopped" }, { key: "chat.errors.stopped" }],
    [{ kind: "network" }, { key: "chat.errors.network" }],
    [{ kind: "stream", code: "llm_timeout", scope: null }, { key: "chat.errors.llm_timeout" }],
    [
      { kind: "stream", code: "quota_exceeded", scope: "global" },
      { key: "chat.errors.quota_exceeded_global" },
    ],
    [{ kind: "stream", code: "quota_exceeded", scope: "user" }, { key: "chat.errors.quota_exceeded" }],
    [
      { kind: "request", code: "quota_exceeded", retryAfter: 3600, scope: "global" },
      { key: "chat.errors.quota_exceeded_global" },
    ],
    [
      { kind: "request", code: "rate_limited", retryAfter: 1260, scope: null },
      { key: "chat.errors.rate_limited_retry", values: { minutes: 21 } },
    ],
    [
      { kind: "request", code: "quota_exceeded", retryAfter: null, scope: "user" },
      { key: "chat.errors.quota_exceeded" },
    ],
    [
      { kind: "request", code: "validation_error", retryAfter: null, scope: null },
      { key: "chat.errors.generic" },
    ],
    [{ kind: "request", code: null, retryAfter: null, scope: null }, { key: "chat.errors.generic" }],
  ] as const)("%o", (failure, expected) => {
    expect(failureMessage(failure)).toEqual(expected);
  });
});

/** Stored failed answers (contract v1.1 `error_code`). */
describe("storedFailureMessage", () => {
  it.each([
    ["stopped", "chat.answerStopped"],
    ["llm_timeout", "chat.errors.llm_timeout"],
    [null, "chat.failedMessage"],
  ] as const)("%s → %s", (code, key) => {
    expect(storedFailureMessage(code)).toEqual({ key });
  });
});
