/** Message for a failed "resend verification" call (screens 3–4). */
import { ApiError } from "../../api/http";
import { retryMinutes } from "../../lib/format";

/** Copy key and values for `t()`. */
export interface ResendFailure {
  key: string;
  values?: Record<string, number>;
  rateLimited: boolean;
}

/**
 * Map a resend error: `429 rate_limited` shows the wait, anything else the server error.
 *
 * @param error What the call threw.
 * @returns Copy key, values and whether resending is blocked for now.
 */
export function resendFailure(error: unknown): ResendFailure {
  if (error instanceof ApiError && error.code === "rate_limited") {
    return {
      key: "check_email.rate_limited",
      values: { minutes: retryMinutes(error.retryAfter ?? 0) },
      rateLimited: true,
    };
  }
  return { key: "error.server", rateLimited: false };
}
