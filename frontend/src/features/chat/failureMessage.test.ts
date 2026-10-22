import { describe, expect, it } from "vitest";
import { failureMessage } from "./failureMessage";

/** Every failure kind maps to an existing message key. */
describe("failureMessage", () => {
  it.each([
    [{ kind: "stopped" }, { key: "chat.errors.stopped" }],
    [{ kind: "network" }, { key: "chat.errors.network" }],
    [{ kind: "stream", code: "llm_timeout" }, { key: "chat.errors.llm_timeout" }],
    [
      { kind: "request", code: "rate_limited", retryAfter: 1260 },
      { key: "chat.errors.rate_limited_retry", values: { minutes: 21 } },
    ],
    [{ kind: "request", code: "quota_exceeded", retryAfter: null }, { key: "chat.errors.quota_exceeded" }],
    [{ kind: "request", code: "validation_error", retryAfter: null }, { key: "chat.errors.generic" }],
    [{ kind: "request", code: null, retryAfter: null }, { key: "chat.errors.generic" }],
  ] as const)("%o", (failure, expected) => {
    expect(failureMessage(failure)).toEqual(expected);
  });
});
