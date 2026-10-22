/**
 * django-allauth headless "browser" client calls (contract §2).
 * allauth answers with its own envelope, not problem+json, so these calls parse it here.
 */
import { csrfToken, send } from "./http";

/** Base path of the allauth browser API. */
export const AUTH_BASE = "/_allauth/browser/v1";

/** One allauth validation error. */
export interface AllauthError {
  message: string;
  code: string;
  param?: string;
}

/** A pending or available auth flow. */
interface AllauthFlow {
  id: string;
  is_pending?: boolean;
}

/** allauth response envelope (subset the SPA reads). */
interface AllauthEnvelope {
  status: number;
  data?: {
    flows?: AllauthFlow[];
    socialaccount?: { providers?: { id: string; name: string }[] };
  };
  errors?: AllauthError[];
}

/** Where the browser session stands. */
export type AuthState = "authenticated" | "pending_verification" | "anonymous";

/** A social login provider enabled on the backend. */
export interface AuthProvider {
  id: string;
  name: string;
}

/** Thrown when allauth rejects the input (HTTP 400) or returns an unexpected status. */
export class AuthError extends Error {
  readonly status: number;
  readonly errors: AllauthError[];

  /**
   * @param status HTTP status code.
   * @param errors allauth error list (may be empty).
   */
  constructor(status: number, errors: AllauthError[]) {
    super(errors[0]?.message ?? `Auth request failed (${status})`);
    this.name = "AuthError";
    this.status = status;
    this.errors = errors;
  }

  /** Error codes, e.g. `["email_password_mismatch"]`. */
  get codes(): string[] {
    return this.errors.map((error) => error.code);
  }
}

/** Statuses that describe the session rather than an error. */
const SESSION_STATUSES = new Set([200, 401, 410]);

/**
 * Map an allauth envelope to a session state.
 *
 * @param envelope Parsed allauth body.
 * @returns `authenticated` on 200, `pending_verification` when email verification is pending, else `anonymous`.
 */
export function authStateOf(envelope: AllauthEnvelope): AuthState {
  if (envelope.status === 200) return "authenticated";
  const pending = envelope.data?.flows?.some((flow) => flow.id === "verify_email" && flow.is_pending);
  return pending ? "pending_verification" : "anonymous";
}

/**
 * Send an allauth request and read the session state from the reply.
 *
 * @param path Path below {@link AUTH_BASE}.
 * @param method HTTP method.
 * @param body JSON body.
 * @returns The resulting session state.
 * @throws {AuthError} On validation errors or unexpected statuses.
 */
async function authCall(path: string, method: string, body?: unknown): Promise<AuthState> {
  const response = await send(`${AUTH_BASE}${path}`, { method, body });
  const envelope = (await response.json()) as AllauthEnvelope;
  if (!SESSION_STATUSES.has(response.status)) {
    throw new AuthError(response.status, envelope.errors ?? []);
  }
  return authStateOf(envelope);
}

/**
 * Current browser session.
 *
 * @returns The session state.
 */
export function getSession(): Promise<AuthState> {
  return authCall("/auth/session", "GET");
}

/**
 * Create an account. With mandatory verification the result is `pending_verification`.
 *
 * @param input Email, password and Turnstile token.
 * @returns The session state after signup.
 */
export function signup(input: {
  email: string;
  password: string;
  turnstile_token: string;
}): Promise<AuthState> {
  return authCall("/auth/signup", "POST", input);
}

/**
 * Log in with email + password.
 *
 * @param input Credentials.
 * @returns The session state after login.
 */
export function login(input: { email: string; password: string }): Promise<AuthState> {
  return authCall("/auth/login", "POST", input);
}

/**
 * End the session. allauth answers 401 on success.
 *
 * @returns The session state (always `anonymous` on success).
 */
export function logout(): Promise<AuthState> {
  return authCall("/auth/session", "DELETE");
}

/**
 * Confirm an email address with the key from the email link.
 *
 * @param key Verification key from `/verify-email/:key`.
 * @returns `authenticated` when allauth also logged the user in, else `anonymous`.
 */
export function verifyEmail(key: string): Promise<AuthState> {
  return authCall("/auth/email/verify", "POST", { key });
}

/**
 * Send a password-reset email.
 *
 * @param email Account email.
 */
export async function requestPasswordReset(email: string): Promise<void> {
  await authCall("/auth/password/request", "POST", { email });
}

/**
 * Set a new password with the key from the reset email.
 *
 * @param input Reset key and new password.
 * @returns The session state after the reset.
 */
export function resetPassword(input: { key: string; password: string }): Promise<AuthState> {
  return authCall("/auth/password/reset", "POST", input);
}

/**
 * Change (or, for Google-only accounts, set) the password. Contract §2: omit `current_password` when
 * `Me.has_password` is false.
 *
 * @param input New password, plus the current one when the account has a password.
 */
export async function changePassword(input: {
  current_password?: string;
  new_password: string;
}): Promise<void> {
  await authCall("/account/password/change", "POST", input);
}

/**
 * Social providers enabled on the backend (`GET /config`).
 *
 * @returns The provider list (empty when social login is off).
 */
export async function getProviders(): Promise<AuthProvider[]> {
  const response = await send(`${AUTH_BASE}/config`);
  if (!response.ok) throw new AuthError(response.status, []);
  const envelope = (await response.json()) as AllauthEnvelope;
  return envelope.data?.socialaccount?.providers ?? [];
}

/**
 * Form fields for the allauth provider-redirect POST (a full-page form submit, not fetch).
 *
 * @param provider Provider id, e.g. `google`.
 * @param callbackUrl SPA URL allauth returns to after the provider.
 * @returns Field name → value pairs, including the CSRF token.
 */
export function providerRedirectFields(provider: string, callbackUrl: string): Record<string, string> {
  return { provider, callback_url: callbackUrl, process: "login", csrfmiddlewaretoken: csrfToken() };
}

/** URL the provider-redirect form posts to. */
export const PROVIDER_REDIRECT_URL = `${AUTH_BASE}/auth/provider/redirect`;
