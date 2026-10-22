/** Which message to show for a failed turn or a failed stored answer. */
import type { AssistantErrorCode, QuotaScope } from "../../api/types";
import { retryMinutes } from "../../lib/format";
import type { TurnFailure } from "./useChatStream";

/** i18n key plus interpolation values. */
export interface FailureMessage {
  key: string;
  values?: Record<string, number>;
}

/** Problem codes with their own chat message (others get the generic one). */
const REQUEST_CODES = new Set(["rate_limited", "quota_exceeded", "stream_in_progress", "llm_unavailable"]);

/**
 * Message key for an error code; the service-wide quota has its own copy (contract v1.1 `scope`).
 *
 * @param code Error code.
 * @param scope Quota scope, when known.
 * @returns The i18n key.
 */
function codeKey(code: string, scope: QuotaScope | null): string {
  return code === "quota_exceeded" && scope === "global"
    ? "chat.errors.quota_exceeded_global"
    : `chat.errors.${code}`;
}

/**
 * Map a live turn failure to a translatable message.
 *
 * @param failure Why the turn failed.
 * @returns Key and values for `t()`.
 */
export function failureMessage(failure: TurnFailure): FailureMessage {
  switch (failure.kind) {
    case "stopped":
      return { key: "chat.errors.stopped" };
    case "network":
      return { key: "chat.errors.network" };
    case "stream":
      return { key: codeKey(failure.code, failure.scope) };
    case "request":
      if (!failure.code || !REQUEST_CODES.has(failure.code)) return { key: "chat.errors.generic" };
      if (failure.scope === "global") return { key: codeKey(failure.code, failure.scope) };
      if (failure.retryAfter !== null) {
        return {
          key: `chat.errors.${failure.code}_retry`,
          values: { minutes: retryMinutes(failure.retryAfter) },
        };
      }
      return { key: `chat.errors.${failure.code}` };
  }
}

/**
 * Map a stored failed answer (`error_code`, contract v1.1) to a translatable message.
 *
 * @param code The message's `error_code`, or `null` when the backend gave none.
 * @returns Key for `t()`.
 */
export function storedFailureMessage(code: AssistantErrorCode | null): FailureMessage {
  if (code === "stopped") return { key: "chat.answerStopped" };
  return { key: code ? `chat.errors.${code}` : "chat.failedMessage" };
}
