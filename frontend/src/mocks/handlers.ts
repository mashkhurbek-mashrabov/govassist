/**
 * MSW handlers for allauth headless (contract §2) and `/api/v1/` (contract §3–§4).
 *
 * Mock-only triggers in the question text: `#limit` → 429 rate_limited, `#quota` → 429 quota_exceeded
 * (scope user), `#globalquota` → 429 quota_exceeded (scope global),
 * `#busy` → 409 stream_in_progress, `#error` → in-stream `error` event, `#offtopic` → off-topic answer.
 * Verification and reset links are printed to the console, like Django's console email backend.
 */
import { http, HttpResponse, type HttpResponseResolver } from "msw";
import { AUTH_BASE } from "../api/auth";
import { API_BASE } from "../api/endpoints";
import { CSRF_HEADER } from "../api/http";
import type { AssistantMessage, Conversation, Feedback, Lang, Me, MeUpdate, Message } from "../api/types";
import { LANGUAGES } from "../i18n";
import { currentUser, db, newUser, sampleAssistantMessage, saveDb, WRONG_PASSWORD } from "./db";
import { SAMPLE_DISTRICTS, SAMPLE_SOURCE_SUMMARIES, SAMPLE_REGIONS, SAMPLE_SUGGESTIONS } from "./fixtures";
import { localizeMe, localizeOffice, localizePlace } from "./localize";
import { scenarioFor } from "./scenarios";
import { errorFrames, raceFrame, sseResponse, successFrames } from "./sse";

/** CSRF token the mock "Django" sets and expects back. */
export const MOCK_CSRF_TOKEN = "mock-csrf-token";
/** Contract limits. */
const MIN_PASSWORD_LENGTH = 10;
const MAX_TEXT_LENGTH = 1000;
const DEFAULT_PAGE_SIZE = 20;
const MAX_PAGE_SIZE = 50;
/** `retry_after` the mock returns for rate limits (seconds). */
const MOCK_RETRY_AFTER = 1260;
/** Max characters of a new conversation's title (from the question, contract v1.4). */
const TITLE_LENGTH = 60;
/** Max characters of a history preview (contract v1.4). */
const PREVIEW_LENGTH = 120;

// ── Response helpers ────────────────────────────────────────────────────────────────────────────

/**
 * RFC 9457 problem response.
 *
 * @param status HTTP status.
 * @param code Contract error code.
 * @param extra Extra fields (`retry_after`, `errors`).
 * @returns The response.
 */
function problem(status: number, code: string, extra: Record<string, unknown> = {}) {
  return HttpResponse.json(
    {
      type: "about:blank",
      title: code,
      status,
      detail: `SAMPLE: ${code}`,
      code,
      retry_after: null,
      errors: null,
      ...extra,
    },
    { status, headers: { "Content-Type": "application/problem+json" } },
  );
}

/**
 * allauth envelope for a signed-in session.
 *
 * @param me The user.
 * @returns 200 response.
 */
function authenticated(me: Me) {
  return HttpResponse.json({
    status: 200,
    data: { user: { id: me.id, email: me.email, display: me.email }, methods: [] },
    meta: { is_authenticated: true },
  });
}

/**
 * allauth envelope for no session, optionally with a pending email verification.
 *
 * @param pending Whether verification is pending.
 * @returns 401 response.
 */
function unauthenticated(pending = false) {
  const flows = [
    { id: "login" },
    { id: "signup" },
    ...(pending ? [{ id: "verify_email", is_pending: true }] : []),
  ];
  return HttpResponse.json(
    { status: 401, data: { flows }, meta: { is_authenticated: false } },
    { status: 401 },
  );
}

/**
 * allauth 400 with one error.
 *
 * @param code allauth error code.
 * @param param Field name.
 * @returns 400 response.
 */
function authError(code: string, param?: string) {
  return HttpResponse.json(
    { status: 400, errors: [{ code, param, message: `SAMPLE: ${code}` }] },
    { status: 400 },
  );
}

/**
 * Whether an unsafe request carries the CSRF header Django expects.
 *
 * @param request Incoming request.
 * @returns `true` when the token matches.
 */
function hasCsrf(request: Request): boolean {
  return request.headers.get(CSRF_HEADER) === MOCK_CSRF_TOKEN;
}

/**
 * Wrap a resolver for unsafe methods with Django's CSRF check (403 on mismatch).
 *
 * @param resolver The real handler.
 * @returns The guarded handler.
 */
function csrf(resolver: HttpResponseResolver): HttpResponseResolver {
  return (info) => (hasCsrf(info.request) ? resolver(info) : problem(403, "csrf_failed"));
}

/**
 * Log a "sent email" link, like Django's console email backend.
 *
 * @param label What the link is for.
 * @param path SPA path with the key.
 */
function logEmail(label: string, path: string): void {
  console.info(`[MSW mail] ${label}: ${location.origin}${path}`);
}

/**
 * Pretend to email a verification link to an address.
 *
 * @param email Address.
 */
function sendVerification(email: string): void {
  const key = emailKey();
  db.verificationKeys[key] = email;
  db.pendingEmail = email;
  logEmail("Verify email", `/verify-email/${encodeURIComponent(key)}`);
}

/**
 * A key shaped like allauth's (`MQ:…`), which contains `:` and is URL-encoded in links (contract v1.3).
 *
 * @returns A new key.
 */
function emailKey(): string {
  return `MQ:${crypto.randomUUID()}`;
}

/**
 * Recompute `profile_complete` after a change.
 *
 * @param me The user to update in place.
 */
function refreshProfileFlag(me: Me): void {
  me.profile_complete = me.region !== null && me.district !== null;
}

/**
 * Validate a PATCH /me body against the geo fixtures.
 *
 * @param me Current user.
 * @param body Requested changes.
 * @returns Field errors (empty when valid).
 */
function validateMeUpdate(me: Me, body: MeUpdate): Record<string, string[]> {
  const errors: Record<string, string[]> = {};
  if (body.ui_language !== undefined && !LANGUAGES.includes(body.ui_language))
    errors.ui_language = ["SAMPLE: invalid"];
  const regionId = body.region_id ?? me.region?.id;
  if (body.region_id !== undefined && !SAMPLE_REGIONS.some((region) => region.id === body.region_id)) {
    errors.region_id = ["SAMPLE: unknown region"];
  }
  // Contract v1.4: changing the region requires a district in the same request.
  if (body.region_id !== undefined && body.region_id !== me.region?.id && body.district_id === undefined) {
    errors.district_id = ["SAMPLE: required when the region changes"];
  }
  if (body.district_id !== undefined) {
    const districts = regionId === undefined ? [] : (SAMPLE_DISTRICTS[regionId] ?? []);
    if (!districts.some((district) => district.id === body.district_id)) {
      errors.district_id = ["SAMPLE: district does not belong to region"];
    }
  }
  return errors;
}

/**
 * The signed-in user's conversation, if it exists.
 *
 * @param me Current user.
 * @param id Conversation id.
 * @returns The conversation or `undefined`.
 */
function ownConversation(me: Me, id: unknown) {
  const conversation = typeof id === "string" ? db.conversations[id] : undefined;
  return conversation?.owner === me.email ? conversation : undefined;
}

/**
 * Strip the mock-only `owner` field.
 *
 * @param conversation Stored conversation.
 * @returns The contract `Conversation`.
 */
function publicConversation({ owner, ...conversation }: Conversation & { owner: string }): Conversation {
  return conversation;
}

/**
 * History preview: the last user message (already scrubbed by the real backend), ≤ 120 chars (contract v1.4).
 *
 * @param messages Conversation messages, oldest first.
 * @returns Preview text.
 */
function preview(messages: Message[]): string {
  const question = messages.findLast((message) => message.role === "user");
  return question?.role === "user" ? question.text.slice(0, PREVIEW_LENGTH) : "";
}

/**
 * Language of localized names: `?lang=`, else the user's `ui_language`, else uz-Latn (contract §1).
 *
 * @param request Incoming request.
 * @returns The language.
 */
function requestLang(request: Request): Lang {
  const param = new URL(request.url).searchParams.get("lang");
  if (param && (LANGUAGES as readonly string[]).includes(param)) return param as Lang;
  return currentUser()?.ui_language ?? "uz-Latn";
}

// ── allauth ─────────────────────────────────────────────────────────────────────────────────────

const authHandlers = [
  http.get(`${AUTH_BASE}/config`, () =>
    HttpResponse.json({
      status: 200,
      data: {
        account: {},
        socialaccount: { providers: [{ id: "google", name: "Google", flows: ["provider_redirect"] }] },
      },
    }),
  ),
  http.get(`${AUTH_BASE}/auth/session`, () => {
    const me = currentUser();
    return me ? authenticated(me) : unauthenticated(db.pendingEmail !== null);
  }),
  http.delete(
    `${AUTH_BASE}/auth/session`,
    csrf(() => {
      db.sessionEmail = null;
      saveDb();
      return unauthenticated();
    }),
  ),
  http.post(
    `${AUTH_BASE}/auth/signup`,
    csrf(async ({ request }) => {
      const body = (await request.json()) as { email?: string; password?: string };
      const email = (body.email ?? "").toLowerCase();
      if (!email.includes("@")) return authError("invalid", "email");
      if ((body.password ?? "").length < MIN_PASSWORD_LENGTH)
        return authError("password_too_short", "password");
      // Contract v1.3: enumeration prevention. An existing email answers exactly like a new signup;
      // the owner gets an "account already exists" email pointing to /forgot-password.
      if (db.users[email]) {
        db.pendingEmail = email;
        saveDb();
        logEmail("Account already exists", "/forgot-password");
        return unauthenticated(true);
      }
      db.users[email] = newUser(email, false);
      sendVerification(email);
      saveDb();
      return unauthenticated(true);
    }),
  ),
  http.post(
    `${AUTH_BASE}/auth/login`,
    csrf(async ({ request }) => {
      const body = (await request.json()) as { email?: string; password?: string };
      const email = (body.email ?? "").toLowerCase();
      const me = db.users[email];
      if (!me || body.password === WRONG_PASSWORD) return authError("email_password_mismatch", "password");
      if (!me.email_verified) {
        sendVerification(email);
        saveDb();
        return unauthenticated(true);
      }
      db.sessionEmail = email;
      saveDb();
      return authenticated(me);
    }),
  ),
  http.post(
    `${AUTH_BASE}/auth/email/verify`,
    csrf(async ({ request }) => {
      const { key = "" } = (await request.json()) as { key?: string };
      const email = db.verificationKeys[key];
      const me = email ? db.users[email] : undefined;
      if (!email || !me) return authError("invalid", "key");
      me.email_verified = true;
      Reflect.deleteProperty(db.verificationKeys, key);
      db.pendingEmail = null;
      db.sessionEmail = email;
      saveDb();
      return authenticated(me);
    }),
  ),
  http.post(
    `${AUTH_BASE}/auth/password/request`,
    csrf(async ({ request }) => {
      const { email = "" } = (await request.json()) as { email?: string };
      if (db.users[email.toLowerCase()]) {
        const key = emailKey();
        db.resetKeys[key] = email.toLowerCase();
        saveDb();
        logEmail("Reset password", `/reset-password/${encodeURIComponent(key)}`);
      }
      return HttpResponse.json({ status: 200 });
    }),
  ),
  http.post(
    `${AUTH_BASE}/auth/password/reset`,
    csrf(async ({ request }) => {
      const body = (await request.json()) as { key?: string; password?: string };
      if (!body.key || !db.resetKeys[body.key]) return authError("invalid", "key");
      if ((body.password ?? "").length < MIN_PASSWORD_LENGTH)
        return authError("password_too_short", "password");
      Reflect.deleteProperty(db.resetKeys, body.key);
      saveDb();
      return unauthenticated();
    }),
  ),
  http.post(
    `${AUTH_BASE}/account/password/change`,
    csrf(async ({ request }) => {
      const me = currentUser();
      if (!me) return unauthenticated();
      const body = (await request.json()) as { current_password?: string; new_password?: string };
      if (me.has_password && (!body.current_password || body.current_password === WRONG_PASSWORD)) {
        return authError("incorrect_password", "current_password");
      }
      if ((body.new_password ?? "").length < MIN_PASSWORD_LENGTH)
        return authError("password_too_short", "new_password");
      me.has_password = true;
      saveDb();
      return HttpResponse.json({ status: 200 });
    }),
  ),
];

// ── App API ─────────────────────────────────────────────────────────────────────────────────────

/**
 * Wrap a resolver that needs a signed-in user (401 problem otherwise).
 *
 * @param resolver Handler receiving the user.
 * @returns The guarded handler.
 */
function withUser(
  resolver: (info: Parameters<HttpResponseResolver>[0], me: Me) => ReturnType<HttpResponseResolver>,
): HttpResponseResolver {
  return (info) => {
    const me = currentUser();
    return me ? resolver(info, me) : problem(401, "not_authenticated");
  };
}

/**
 * The mock `POST /chat`: checks, then a streamed answer that is stored like the real backend would.
 *
 * @param request Incoming request.
 * @param me Signed-in user.
 * @returns A problem response or the SSE stream.
 */
async function chat(request: Request, me: Me) {
  if (!me.email_verified) return problem(403, "email_not_verified");
  if (!me.profile_complete) return problem(403, "profile_incomplete");
  const body = (await request.json()) as { conversation_id: string | null; text: string };
  const text = body.text.trim();
  if (text.length === 0 || text.length > MAX_TEXT_LENGTH) {
    return problem(400, "validation_error", { errors: { text: ["SAMPLE: 1–1000 characters"] } });
  }
  if (text.includes("#limit")) {
    return HttpResponse.json(
      {
        type: "about:blank",
        title: "Too many requests",
        status: 429,
        detail: "SAMPLE",
        code: "rate_limited",
        retry_after: MOCK_RETRY_AFTER,
        errors: null,
      },
      {
        status: 429,
        headers: { "Content-Type": "application/problem+json", "Retry-After": String(MOCK_RETRY_AFTER) },
      },
    );
  }
  if (text.includes("#quota")) return problem(429, "quota_exceeded", { scope: "user" });
  if (text.includes("#globalquota")) return problem(429, "quota_exceeded", { scope: "global" });
  if (text.includes("#busy")) return problem(409, "stream_in_progress");
  // Contract v1.6: another stream won the lock race; `error` is the only event and nothing is stored.
  if (text.includes("#race")) return sseResponse([raceFrame()]);

  const now = new Date().toISOString();
  let conversation = body.conversation_id ? ownConversation(me, body.conversation_id) : undefined;
  if (body.conversation_id && !conversation) return problem(404, "not_found");
  if (!conversation) {
    const id = crypto.randomUUID();
    conversation = {
      id,
      owner: me.email,
      title: text.slice(0, TITLE_LENGTH),
      created_at: now,
      updated_at: now,
      messages: [],
    };
    db.conversations[id] = conversation;
  }
  const meta = {
    conversation_id: conversation.id,
    user_message_id: crypto.randomUUID(),
    assistant_message_id: crypto.randomUUID(),
  };
  const scenario = scenarioFor(text);
  const office = scenario.office && localizeOffice(scenario.office, me.ui_language);
  const final: AssistantMessage = {
    ...sampleAssistantMessage(meta.assistant_message_id),
    created_at: now,
    answer: scenario.answer,
    sources: scenario.sources,
    office,
  };
  const stored: AssistantMessage = {
    ...final,
    status: text.includes("#error") ? "failed" : "streaming",
    error_code: text.includes("#error") ? "llm_unavailable" : null,
    answer: null,
  };
  conversation.messages.push({ id: meta.user_message_id, role: "user", text, created_at: now }, stored);
  conversation.updated_at = now;
  me.quota.hour_used += 1;
  me.quota.day_used += 1;
  saveDb();

  if (text.includes("#error")) return sseResponse(errorFrames(meta));
  return sseResponse(successFrames(meta, final, office), {
    onComplete: () => {
      Object.assign(stored, final);
      // Contract v1.4: the first successful answer's title replaces the question-based title.
      if (
        conversation.messages.filter(
          (message) => message.role === "assistant" && message.status === "complete",
        ).length === 1
      ) {
        conversation.title = final.answer?.title ?? conversation.title;
      }
      saveDb();
    },
    onAbort: () => {
      // Contract v1.1 Stop: failed + error_code "stopped", the partial answer is not stored.
      Object.assign(stored, { status: "failed", error_code: "stopped", answer: null });
      saveDb();
    },
  });
}

/** Mock rate limit for verification resends (seconds). */
const RESEND_COOLDOWN_S = 60;
/** Milliseconds per second. */
const MS_PER_S = 1000;

const apiHandlers = [
  http.post(
    `${API_BASE}/auth/resend-verification`,
    csrf(async ({ request }) => {
      const { email = "" } = (await request.json()) as { email?: string };
      const now = Date.now();
      if (db.lastResendAt !== null && now - db.lastResendAt < RESEND_COOLDOWN_S * MS_PER_S) {
        return problem(429, "rate_limited", { retry_after: RESEND_COOLDOWN_S });
      }
      db.lastResendAt = now;
      if (db.users[email.toLowerCase()]?.email_verified === false) sendVerification(email.toLowerCase());
      saveDb();
      return new HttpResponse(null, { status: 204 });
    }),
  ),
  http.get(`${API_BASE}/sources`, () => HttpResponse.json({ items: SAMPLE_SOURCE_SUMMARIES })),
  http.get(`${API_BASE}/health`, () =>
    HttpResponse.json({ status: "ok", checks: { db: "ok", redis: "ok" } }),
  ),
  http.get(
    `${API_BASE}/csrf`,
    () =>
      new HttpResponse(null, {
        status: 204,
        headers: { "Set-Cookie": `csrftoken=${MOCK_CSRF_TOKEN}; Path=/` },
      }),
  ),
  http.get(
    `${API_BASE}/me`,
    withUser((_info, me) => HttpResponse.json(localizeMe(me))),
  ),
  http.patch(
    `${API_BASE}/me`,
    csrf(
      withUser(async ({ request }, me) => {
        const body = (await request.json()) as MeUpdate;
        const errors = validateMeUpdate(me, body);
        if (Object.keys(errors).length > 0) return problem(400, "validation_error", { errors });
        if (body.ui_language) me.ui_language = body.ui_language;
        if (body.display_name !== undefined) me.display_name = body.display_name || null;
        if (body.region_id !== undefined)
          me.region = SAMPLE_REGIONS.find((region) => region.id === body.region_id) ?? null;
        if (body.district_id !== undefined && me.region) {
          me.district =
            SAMPLE_DISTRICTS[me.region.id]?.find((district) => district.id === body.district_id) ?? null;
        }
        refreshProfileFlag(me);
        saveDb();
        return HttpResponse.json(localizeMe(me));
      }),
    ),
  ),
  http.delete(
    `${API_BASE}/me`,
    csrf(
      withUser(async ({ request }, me) => {
        const body = (await request.json()) as { confirm?: boolean };
        if (body.confirm !== true)
          return problem(400, "validation_error", { errors: { confirm: ["SAMPLE: required"] } });
        Reflect.deleteProperty(db.users, me.email);
        for (const [id, conversation] of Object.entries(db.conversations)) {
          if (conversation.owner === me.email) Reflect.deleteProperty(db.conversations, id);
        }
        db.sessionEmail = null;
        saveDb();
        return new HttpResponse(null, { status: 204 });
      }),
    ),
  ),
  http.get(`${API_BASE}/geo/regions`, ({ request }) => {
    const lang = requestLang(request);
    return HttpResponse.json(SAMPLE_REGIONS.map((region) => localizePlace(region, lang)));
  }),
  http.get(`${API_BASE}/geo/regions/:regionId/districts`, ({ request, params }) => {
    const districts = SAMPLE_DISTRICTS[Number(params.regionId)];
    const lang = requestLang(request);
    return districts
      ? HttpResponse.json(districts.map((district) => localizePlace(district, lang)))
      : problem(404, "not_found");
  }),
  http.get(
    `${API_BASE}/suggestions`,
    withUser(() => HttpResponse.json({ items: SAMPLE_SUGGESTIONS })),
  ),
  http.get(
    `${API_BASE}/conversations`,
    withUser(({ request }, me) => {
      const url = new URL(request.url);
      const offset = Number(url.searchParams.get("cursor") ?? 0);
      const limit = Math.min(Number(url.searchParams.get("limit") ?? DEFAULT_PAGE_SIZE), MAX_PAGE_SIZE);
      const own = Object.values(db.conversations)
        .filter((conversation) => conversation.owner === me.email)
        .sort((a, b) => b.updated_at.localeCompare(a.updated_at));
      const results = own.slice(offset, offset + limit).map((conversation) => ({
        id: conversation.id,
        title: conversation.title,
        updated_at: conversation.updated_at,
        last_message_preview: preview(conversation.messages),
      }));
      const next = offset + limit < own.length ? String(offset + limit) : null;
      return HttpResponse.json({ results, next });
    }),
  ),
  http.get(
    `${API_BASE}/conversations/:id`,
    withUser(({ params }, me) => {
      const conversation = ownConversation(me, params.id);
      return conversation ? HttpResponse.json(publicConversation(conversation)) : problem(404, "not_found");
    }),
  ),
  http.delete(
    `${API_BASE}/conversations/:id`,
    csrf(
      withUser(({ params }, me) => {
        const conversation = ownConversation(me, params.id);
        if (!conversation) return problem(404, "not_found");
        Reflect.deleteProperty(db.conversations, conversation.id);
        saveDb();
        return new HttpResponse(null, { status: 204 });
      }),
    ),
  ),
  http.post(`${API_BASE}/chat`, csrf(withUser(({ request }, me) => chat(request, me)))),
  http.post(
    `${API_BASE}/messages/:id/feedback`,
    csrf(
      withUser(async ({ request, params }, me) => {
        const body = (await request.json()) as Partial<Feedback>;
        if ((body.rating !== 1 && body.rating !== -1) || (body.comment ?? "").length > MAX_TEXT_LENGTH) {
          return problem(400, "validation_error", { errors: { rating: ["SAMPLE: 1 or -1"] } });
        }
        const message = Object.values(db.conversations)
          .filter((conversation) => conversation.owner === me.email)
          .flatMap((conversation) => conversation.messages)
          .find(
            (candidate): candidate is AssistantMessage =>
              candidate.id === params.id && candidate.role === "assistant",
          );
        if (!message) return problem(404, "not_found");
        const created = message.feedback === null;
        message.feedback = { rating: body.rating, comment: body.comment ?? "" };
        saveDb();
        return HttpResponse.json(message.feedback, { status: created ? 201 : 200 });
      }),
    ),
  ),
];

/** Every mock handler. */
export const handlers = [...authHandlers, ...apiHandlers];
