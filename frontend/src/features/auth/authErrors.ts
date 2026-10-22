/** allauth error codes → copy keys and the field they belong to (copy.md → Error codes; contract §2). */
import { AuthError } from "../../api/auth";

/** A translated auth error and where to show it. */
export interface AuthErrorInfo {
  /** copy.md key. */
  key: string;
  /** Form field (allauth `param`), or `null` for a form-level alert. */
  field: "email" | "password" | "turnstile_token" | "current_password" | null;
  /** Whether the alert is a warning (rate limits) rather than an error. */
  warning: boolean;
}

/** Known codes. Unknown codes fall back to `error.server`; allauth's raw `message` is never shown. */
const CODES: Record<string, Omit<AuthErrorInfo, "field"> & { field?: AuthErrorInfo["field"] }> = {
  turnstile_failed: { key: "error.turnstile", field: "turnstile_token", warning: false },
  email_password_mismatch: { key: "error.login_failed", warning: false },
  too_many_login_attempts: { key: "error.too_many_logins", warning: true },
  password_too_short: { key: "error.password_short", field: "password", warning: false },
  password_too_common: { key: "error.password_common", field: "password", warning: false },
  password_entirely_numeric: { key: "error.password_numeric", field: "password", warning: false },
  enter_current_password: { key: "error.current_password_wrong", field: "current_password", warning: false },
};

/** Generic field codes (contract v1.9): the copy depends on the field named by `param`. */
const FIELD_CODES: Record<string, Partial<Record<NonNullable<AuthErrorInfo["field"]>, string>>> = {
  required: { email: "error.required", password: "error.required", current_password: "error.required" },
  invalid: { email: "error.email_invalid" },
};

/** Fallback for unknown codes and non-allauth failures. */
const SERVER_ERROR: AuthErrorInfo = { key: "error.server", field: null, warning: false };

/** allauth's rate limit: a bare `429 {"status": 429}` with no `errors` (contract v1.8). */
const RATE_LIMITED: AuthErrorInfo = { key: "error.too_many_attempts", field: null, warning: true };

/** HTTP status of allauth's rate limit. */
const TOO_MANY_REQUESTS = 429;

/**
 * Describe the first known error of a failed auth call.
 *
 * @param error Whatever the call threw.
 * @returns Copy key, target field and tone.
 */
export function authErrorInfo(error: unknown): AuthErrorInfo {
  if (!(error instanceof AuthError)) return SERVER_ERROR;
  if (error.status === TOO_MANY_REQUESTS) return RATE_LIMITED;
  for (const item of error.errors) {
    const known = CODES[item.code];
    if (known) return { key: known.key, warning: known.warning, field: known.field ?? null };
    const byField = FIELD_CODES[item.code];
    const field = item.param as NonNullable<AuthErrorInfo["field"]> | undefined;
    const key = field && byField?.[field];
    if (field && key) return { key, field, warning: false };
  }
  return SERVER_ERROR;
}
