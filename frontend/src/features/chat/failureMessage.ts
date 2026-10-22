/** Which message to show for a failed turn. */
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
 * Map a turn failure to a translatable message.
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
      return { key: `chat.errors.${failure.code}` };
    case "request":
      if (!failure.code || !REQUEST_CODES.has(failure.code)) return { key: "chat.errors.generic" };
      if (failure.retryAfter !== null) {
        return {
          key: `chat.errors.${failure.code}_retry`,
          values: { minutes: retryMinutes(failure.retryAfter) },
        };
      }
      return { key: `chat.errors.${failure.code}` };
  }
}
