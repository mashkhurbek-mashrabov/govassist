/** Which alert to show for a failed answer (screen 12; copy.md → Error codes). */
import type { AssistantErrorCode } from "../../api/types";
import { retryMinutes } from "../../lib/format";
import type { TurnFailure } from "./useChatStream";

/** A translatable failure alert. */
export interface FailureMessage {
  titleKey: string;
  key: string;
  values?: Record<string, number>;
  tone: "danger" | "warning";
  /** Whether Retry makes sense (not for limits: they need waiting). */
  retry: boolean;
}

/** Codes with their own `chat_error.*` copy. */
const OWN_COPY = new Set(["llm_unavailable", "llm_timeout", "invalid_answer", "stream_in_progress"]);

/**
 * Alert for an error code.
 *
 * @param code Contract error code (`null` when unknown).
 * @param scope Quota scope, for `quota_exceeded`.
 * @param retryAfter Seconds to wait, for `rate_limited`.
 * @param hourLimit `Me.quota.hour_limit`, shown in the rate-limit copy.
 * @returns Copy keys, values, tone and the Retry flag.
 */
function codeMessage(
  code: string | null,
  scope: string | null,
  retryAfter: number | null,
  hourLimit: number,
): FailureMessage {
  const base = { titleKey: "chat_error.title" };
  if (code === "rate_limited") {
    const values = { limit: hourLimit, minutes: retryMinutes(retryAfter ?? 0) };
    return { ...base, key: "chat_error.rate_limited", values, tone: "warning", retry: false };
  }
  if (code === "quota_exceeded") {
    return {
      ...base,
      key: scope === "global" ? "chat_error.quota_global" : "chat_error.quota_user",
      tone: "warning",
      retry: false,
    };
  }
  if (code === "stream_in_progress")
    return { ...base, key: "chat_error.stream_in_progress", tone: "warning", retry: true };
  if (code && OWN_COPY.has(code)) return { ...base, key: `chat_error.${code}`, tone: "danger", retry: true };
  return { ...base, key: "error.server", tone: "danger", retry: true };
}

/**
 * Alert for a live turn that failed (the user's own Stop is shown by the progress line instead).
 *
 * @param failure Why the turn failed.
 * @param hourLimit `Me.quota.hour_limit`.
 * @returns The alert content.
 */
export function failureMessage(
  failure: Exclude<TurnFailure, { kind: "stopped" }>,
  hourLimit: number,
): FailureMessage {
  switch (failure.kind) {
    case "network":
      return codeMessage(null, null, null, hourLimit);
    case "stream":
      return codeMessage(failure.code, failure.scope, null, hourLimit);
    case "request":
      return codeMessage(failure.code, failure.scope, failure.retryAfter, hourLimit);
  }
}

/**
 * Alert for a stored failed answer (`error_code`, e.g. after a reload).
 *
 * @param code The message's `error_code`.
 * @param hourLimit `Me.quota.hour_limit`.
 * @returns The alert content.
 */
export function storedFailureMessage(code: AssistantErrorCode | null, hourLimit: number): FailureMessage {
  if (code === "stopped") {
    return { titleKey: "chat_error.stopped_title", key: "chat_error.stopped", tone: "warning", retry: true };
  }
  return codeMessage(code, null, null, hourLimit);
}
