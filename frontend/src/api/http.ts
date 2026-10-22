import type { Problem } from "./types";

/** Cookie Django sets on `GET /api/v1/csrf`. */
const CSRF_COOKIE = "csrftoken";
/** Header Django reads the CSRF token from. */
export const CSRF_HEADER = "X-CSRFToken";
/** Methods that need no CSRF token. */
const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

/** Options for {@link send} and {@link request}. */
export interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

/** Error thrown for any non-2xx response. Carries the parsed problem+json when there is one. */
export class ApiError extends Error {
  readonly status: number;
  readonly problem: Problem | null;

  /**
   * @param status HTTP status code.
   * @param problem Parsed problem body, or `null` when the body was not problem+json.
   */
  constructor(status: number, problem: Problem | null) {
    super(problem?.detail ?? problem?.title ?? `HTTP ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.problem = problem;
  }

  /** Machine-readable error code (`rate_limited`, …), or `null` when unknown. */
  get code(): string | null {
    return this.problem?.code ?? null;
  }

  /** Seconds until a retry makes sense, from the problem body. */
  get retryAfter(): number | null {
    return this.problem?.retry_after ?? null;
  }
}

/** Called when the app API answers 401: the session is gone. */
let unauthorizedHandler: (() => void) | null = null;

/**
 * Register what happens on a 401 from the app API (log out + go to `/login`).
 *
 * @param handler Callback, or `null` to clear it.
 */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler;
}

/**
 * Read a cookie value by name.
 *
 * @param name Cookie name.
 * @returns The decoded value, or `null` when the cookie is not set.
 */
export function readCookie(name: string): string | null {
  const prefix = `${name}=`;
  const match = document.cookie.split("; ").find((part) => part.startsWith(prefix));
  return match ? decodeURIComponent(match.slice(prefix.length)) : null;
}

/**
 * Current CSRF token from the `csrftoken` cookie.
 *
 * @returns The token, or an empty string before `GET /csrf` ran.
 */
export function csrfToken(): string {
  return readCookie(CSRF_COOKIE) ?? "";
}

/**
 * Low-level same-origin fetch: JSON body, CSRF header on unsafe methods. Does not check the status.
 *
 * @param path Absolute same-origin path, e.g. `/api/v1/me`.
 * @param options Method, JSON body, extra headers, abort signal.
 * @returns The raw response.
 */
export function send(path: string, options: RequestOptions = {}): Promise<Response> {
  const method = (options.method ?? "GET").toUpperCase();
  const headers: Record<string, string> = { Accept: "application/json", ...options.headers };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (!SAFE_METHODS.has(method)) headers[CSRF_HEADER] = csrfToken();
  return fetch(path, {
    method,
    headers,
    credentials: "same-origin",
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  });
}

/**
 * Turn a failed response into an {@link ApiError}, parsing problem+json when present.
 *
 * @param response A non-2xx response.
 * @returns The error to throw.
 */
export async function toApiError(response: Response): Promise<ApiError> {
  const type = response.headers.get("Content-Type") ?? "";
  const problem = type.includes("json") ? ((await response.json()) as Problem) : null;
  return new ApiError(response.status, problem);
}

/**
 * Pass a successful response through; otherwise run the 401 handler and throw.
 *
 * @param response Any response from the app API.
 * @returns The same response when it is 2xx.
 * @throws {ApiError} For any non-2xx status.
 */
export async function ensureOk(response: Response): Promise<Response> {
  if (response.ok) return response;
  if (response.status === 401) unauthorizedHandler?.();
  throw await toApiError(response);
}

/**
 * Call the app API (`/api/v1/`) and parse the JSON body.
 *
 * @param path Absolute same-origin path.
 * @param options Method, JSON body, extra headers, abort signal.
 * @returns The parsed JSON body, or `undefined` for 204.
 * @throws {ApiError} For any non-2xx status.
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await ensureOk(await send(path, options));
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
