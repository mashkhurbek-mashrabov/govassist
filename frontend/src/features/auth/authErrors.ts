/** Map allauth error codes to i18n keys. */
import { AuthError } from "../../api/auth";

/**
 * allauth error codes → message keys (contract v1.2 §2 "Auth errors", plus allauth's key and
 * current-password codes). Unknown codes fall back to a generic message; allauth's raw `message` is never shown.
 */
const AUTH_ERROR_KEYS: Record<string, string> = {
  email_password_mismatch: "auth.errors.invalidCredentials",
  email_taken: "auth.errors.emailTaken",
  too_many_login_attempts: "auth.errors.tooManyAttempts",
  password_too_short: "auth.errors.weakPassword",
  password_too_common: "auth.errors.weakPassword",
  password_entirely_numeric: "auth.errors.weakPassword",
  password_too_similar: "auth.errors.weakPassword",
  incorrect_password: "auth.errors.incorrectPassword",
  invalid: "auth.errors.invalidKey",
  invalid_or_expired_key: "auth.errors.invalidKey",
  turnstile_failed: "auth.errors.turnstile",
};

/**
 * The i18n key to show for a failed auth call.
 *
 * @param error Whatever the call threw.
 * @returns A message key (generic when the code is unknown or the error is not an `AuthError`).
 */
export function authErrorKey(error: unknown): string {
  if (!(error instanceof AuthError)) return "auth.errors.generic";
  const known = error.codes.map((code) => AUTH_ERROR_KEYS[code]).find(Boolean);
  return known ?? "auth.errors.generic";
}
