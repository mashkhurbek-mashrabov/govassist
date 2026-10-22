# GovAssist API Contract (v1)

**Owner:** main session. Backend and frontend both build against this file.
**Changes:** only by a PR reviewed by the main session. Bump the version note at the bottom.
**Generated artifacts:** the backend exports `docs/schema/openapi.json` and `docs/schema/answer.schema.json` (`invoke schema`). If a generated file disagrees with this document, that is a bug. Fix the code or update the contract, never silently diverge.

---

## 1. Conventions

- **Origin:** a single origin. The SPA, API, auth and admin are all served behind the same host by nginx, so there is **no CORS**.
- **Prefixes:**
  - App API: `/api/v1/`.
  - Auth: `/_allauth/browser/v1/` (django-allauth headless, "browser" client).
  - Admin: path from `ADMIN_URL`.
- **Format:**
  - JSON, `snake_case` keys.
  - IDs are UUID strings, except geo IDs, which are integer SOATO codes.
  - Timestamps are ISO 8601 UTC (`2026-10-22T09:15:00Z`).
  - Dates are `YYYY-MM-DD`.
  - Times of day are `HH:MM` in `Asia/Tashkent`.
- **Languages:** `uz-Latn` | `uz-Cyrl` | `ru` | `en`. Localized names follow `?lang=`, else the user's `ui_language`, else `Accept-Language`, else `uz-Latn`.
- **Auth:**
  - Django session cookie (`sessionid`: HttpOnly, Secure, SameSite=Lax).
  - The SPA calls `GET /api/v1/csrf` once on boot. On every non-GET request it then sends the `csrftoken` cookie value in the `X-CSRFToken` header.
  - Requests use `credentials: "same-origin"`. No tokens in localStorage.
- **Pagination:** cursor-based. The query takes `?cursor=&limit=` (default 20, max 50). The response is `{ "results": [...], "next": "<cursor>" | null }`.
- **Errors:** RFC 9457 `application/problem+json`:

```json
{ "type": "about:blank", "title": "Too many requests", "status": 429,
  "detail": "Hourly question limit reached.", "code": "rate_limited",
  "retry_after": 1260, "errors": null }
```

| `code` | Status | Meaning |
|---|---|---|
| `not_authenticated` | 401 | No session |
| `email_not_verified` | 403 | Email not verified yet |
| `profile_incomplete` | 403 | Region/district missing; go to onboarding |
| `csrf_failed` | 403 | Missing or invalid CSRF token, on DRF views **and** on the `/chat` view. The SPA refetches `GET /api/v1/csrf` and retries once |
| `permission_denied` | 403 | Any other forbidden action |
| `validation_error` | 400 | `errors`: `{field: [messages]}` |
| `rate_limited` | 429 | Per-user/IP limit; `retry_after` seconds; also a `Retry-After` header |
| `quota_exceeded` | 429 | Daily limit reached. The body includes `scope`: `"user"` (this user's daily limit) or `"global"` (the service-wide daily token cap) |
| `stream_in_progress` | 409 | The user already has an answer streaming |
| `not_found` | 404 | Resource missing or not the user's own |
| `llm_unavailable` | 503 | Gemini failed before streaming started |
| `internal_error` | 500 | Unexpected error |

- `retry_after` (seconds) is present only on `rate_limited` and `quota_exceeded`, and omitted otherwise.
- **Every error under `/api/` is problem+json, never Django HTML.** That includes a 404 for a malformed id (e.g. a non-UUID), CSRF failures and 500s.

---

## 2. Auth (django-allauth headless, browser client)

Request and response shapes follow **allauth's own spec**. In dev it is served at `/_allauth/openapi.html` (`HEADLESS_SERVE_SPECIFICATION=True`). The SPA uses these endpoints:

| Purpose | Method + path |
|---|---|
| Config (enabled providers etc.) | `GET /_allauth/browser/v1/config` |
| Current session | `GET /_allauth/browser/v1/auth/session` |
| Log out | `DELETE /_allauth/browser/v1/auth/session` |
| Sign up | `POST /_allauth/browser/v1/auth/signup` `{email, password, turnstile_token}` |
| Log in | `POST /_allauth/browser/v1/auth/login` `{email, password}` |
| Verify email | `POST /_allauth/browser/v1/auth/email/verify` `{key}` |
| Request password reset | `POST /_allauth/browser/v1/auth/password/request` `{email}` |
| Reset password | `POST /_allauth/browser/v1/auth/password/reset` `{key, password}` |
| Google login | `POST /_allauth/browser/v1/auth/provider/redirect` (form post: `provider=google`, `callback_url`, `process=login`) |
| Change / set password | `POST /_allauth/browser/v1/account/password/change` `{current_password, new_password}`. Omit `current_password` when `Me.has_password` is false (Google-only account setting a first password) |

**Auth errors.** allauth returns `400 {"status": 400, "errors": [{"message": str, "code": str, "param": str?}]}`. The SPA maps `code` to an i18n message and falls back to a generic error for unknown codes. It never shows `message` raw.

| `code` | `param` | When |
|---|---|---|
| `turnstile_failed` | `turnstile_token` | Turnstile verification failed or the token is missing (**our** code, set by the backend) |
| `email_password_mismatch` | — | Wrong email or password at login |
| `too_many_login_attempts` | — | allauth login rate limit |
| `password_too_short`, `password_too_common`, `password_entirely_numeric` | `password` | Django password validators (confirmed on allauth 65.20) |

**Account enumeration prevention is on.** Signing up with an email that already exists answers exactly like a new signup: `401` with a pending `verify_email` flow, so the SPA shows "Check your email". The address's owner gets an "account already exists" email with a password-reset link. There is no `email_taken` error.

To resend the verification email, use the app endpoint `POST /api/v1/auth/resend-verification` (§3). To "use another email" before verification, go back to `/signup`; there is no change-email endpoint.

`turnstile_token` is a Cloudflare Turnstile token. The backend verifies it during signup. In dev, a Turnstile test key always passes.

Frontend URLs that allauth puts in emails and redirects (`HEADLESS_FRONTEND_URLS`):

| Key | SPA route |
|---|---|
| `account_confirm_email` | `/verify-email/{key}` |
| `account_reset_password_from_key` | `/reset-password/{key}` |
| `account_reset_password` | `/forgot-password` (the "request a reset" page, linked from the "account already exists" email) |
| `account_signup` | `/signup` |
| `socialaccount_login_error` | `/login?error=social` |

Keys in email links are URL-encoded (e.g. `MQ%3A…`). The SPA must POST the **decoded** key. Check whether the router already decodes the route param, and test with a key that contains `%3A`.

---

## 3. App endpoints (`/api/v1/`)

| Method | Path | Auth | Body | Response |
|---|---|---|---|---|
| GET | `/health` | public | — | `200 {"status":"ok","checks":{"db":"ok","redis":"ok"}}` or `503` with the failing checks |
| GET | `/csrf` | public | — | `204` (sets the `csrftoken` cookie) |
| POST | `/auth/resend-verification` | public | `{"email": str}` | `204` **always**, so it can't reveal whether an account exists. `429 rate_limited` with `retry_after` |
| GET | `/sources` | public | — | `{"items": [SourceSummary]}`: approved, active sources with at least one approved document or office (About page) |
| GET | `/me` | user | — | `Me` |
| PATCH | `/me` | user | `{ui_language?, region_id?, district_id?, display_name?}` | `Me`. `district_id` must belong to `region_id`. Changing `region_id` **requires** `district_id` in the same request; otherwise `400 validation_error` |
| DELETE | `/me` | user | `{"confirm": true}` | `204`. Deletes the account and all its conversations |
| GET | `/geo/regions` | public | — | `[Region]` |
| GET | `/geo/regions/{region_id}/districts` | public | — | `[District]`; `404 not_found` for an unknown region |
| GET | `/suggestions` | user | — | `{"items": [{"text": str, "category": str}]}`, at most 6, in `ui_language` |
| GET | `/conversations` | user | — | paginated `[ConversationSummary]`, newest first |
| GET | `/conversations/{id}` | user | — | `Conversation` (with `messages`) |
| DELETE | `/conversations/{id}` | user | — | `204` |
| POST | `/chat` | user, verified, profile complete | `{"conversation_id": uuid \| null, "text": str}` (1–1000 chars) | **SSE stream** (§4). Errors raised before the stream starts come back as normal problem+json |
| POST | `/messages/{id}/feedback` | user | `{"rating": 1 \| -1, "comment": str?}` (≤ 1000 chars) | `201` on create, `200` on update: `Feedback` |

### Objects

```jsonc
// Me
{ "id": "uuid", "email": "user@example.com", "email_verified": true, "has_password": true,
  "display_name": null, "ui_language": "uz-Latn",
  "region": { "id": 1726, "name": "Toshkent shahri" },        // null until onboarding
  "district": { "id": 1726269, "name": "Chilonzor tumani" },  // null until onboarding
  "profile_complete": true,
  "quota": { "hour_limit": 20, "hour_used": 3, "day_limit": 100, "day_used": 10 } }

// Region / District
{ "id": 1726, "name": "Toshkent shahri" }
{ "id": 1726269, "name": "Chilonzor tumani" }

// ConversationSummary
{ "id": "uuid", "title": "Pasportni almashtirish", "updated_at": "…", "last_message_preview": "…" }
// title: never empty. Set from the scrubbed first question (≤ 60 chars) when the conversation is created,
//        then replaced by the first successful answer's `title`.
// last_message_preview: the last USER message (scrubbed), ≤ 120 chars.

// Conversation
{ "id": "uuid", "title": "…", "created_at": "…", "updated_at": "…", "messages": [Message] }

// Message (user)
{ "id": "uuid", "role": "user", "text": "Pasportimni qanday yangilayman?", "created_at": "…" }

// Message (assistant)
{ "id": "uuid", "role": "assistant", "created_at": "…", "status": "complete",   // "streaming" | "complete" | "failed"
  "error_code": null,   // set when status is "failed": "stopped" | "llm_unavailable" | "llm_timeout" | "invalid_answer" | "quota_exceeded" | "internal_error"
  "answer": Answer | null, "sources": [Source], "office": OfficeMatch | null,
  "refused": false, "feedback": Feedback | null }

// Feedback
{ "rating": 1, "comment": "" }

// SourceSummary (GET /sources)
{ "publisher": "lex.uz", "name": "NAMUNA Oila kodeksi", "kind": "law",   // "law" | "service_page" | "office" | "other"
  "url": "https://lex.uz/", "documents": 12, "last_fetched_at": "2026-10-20T08:00:00Z" }   // last_fetched_at: string | null (the UI hides the date when null)
```

User text is stored **after PII scrubbing**. The history therefore shows placeholders such as `[PASSPORT]`, `[PINFL]`, `[PHONE]` and `[EMAIL]`.

The geo IDs in the examples are illustrative. Real IDs come from the official SOATO classifier.

---

## 4. Chat stream (`POST /api/v1/chat`)

Response headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`.
The browser reads the stream with `fetch` + `ReadableStream`, not `EventSource`, because the request is a POST.

### Events, in order

`meta` → `status`* → `office`? → `delta`* → `final` → `done`.
`error` can replace everything after `meta` and ends the stream.
A keep-alive comment `: ping` is sent every 15 s.

| Event | `data` | Notes |
|---|---|---|
| `meta` | `{"conversation_id": uuid, "user_message_id": uuid, "assistant_message_id": uuid}` | Always first. A new conversation is created when `conversation_id` was null |
| `status` | `{"stage": "searching" \| "found" \| "writing", "source_count": int?}` | For the progress line. Can repeat |
| `office` | `OfficeMatch` | At most once, before the first `delta`. Sent only when a retrieved service maps to an office type |
| `delta` | `{"text": "<raw JSON fragment>"}` | Concatenate all fragments to get a growing, partial `Answer` JSON. Parse it with a partial-JSON parser |
| `final` | `{"message": Message (assistant)}` | Validated answer, resolved `sources`, `office`, `refused`. **Replaces** the live-parsed answer |
| `error` | `{"code": "llm_unavailable" \| "llm_timeout" \| "invalid_answer" \| "quota_exceeded" \| "internal_error", "message": str, "scope"?: "user" \| "global"}` | The assistant message is stored with `status: "failed"` and `error_code` = `code`. `scope` is present only for `quota_exceeded` |
| `done` | `{}` | Last event on success |

**Stop:** the client aborts the request. The backend detects the disconnect and stores the assistant message with `status: "failed"`, `error_code: "stopped"` and `answer: null`. The partial answer is **not** stored. The UI keeps the partial cards on screen for the current view only. After a reload, history shows "Answer stopped" with Retry. **Retry** sends the same text again as a new `POST /chat`, so history keeps both attempts (the stopped one and the retried one). That is intended.

Example wire format:

```
event: meta
data: {"conversation_id":"6f1…","user_message_id":"a12…","assistant_message_id":"b34…"}

event: status
data: {"stage":"searching"}

event: status
data: {"stage":"found","source_count":4}

event: office
data: {"match":"district","office_type":{"code":"public_service_center","label":"Davlat xizmatlari markazi"},"office":{…}}

event: status
data: {"stage":"writing"}

event: delta
data: {"text":"{\"answer_type\":\"service\",\"language\":\"uz-Latn\",\"title\":\"Pasportni alm"}

: ping

event: final
data: {"message":{…}}

event: done
data: {}
```

---

## 5. Answer schema

The same schema is sent to Gemini as `response_schema` and validated with Pydantic on the backend. **Field order is fixed** so that the summary streams first. Every field is always present: arrays may be empty, and `fee`/`processing_time` may be null.

```ts
type Lang = "uz-Latn" | "uz-Cyrl" | "ru" | "en";

interface Answer {
  answer_type: "service" | "legal" | "not_found" | "off_topic";
  language: Lang;                 // language/script of the user's question
  title: string;                  // ≤ 80 chars
  summary: string;                // 1–2 plain sentences
  steps: Item[];                  // ≤ 7. service: procedure; legal: what to do next
  documents: Item[];              // service only: required documents
  fee: Item | null;
  processing_time: Item | null;
  law_points: LawPoint[];         // legal (allowed in service too)
  follow_up_questions: string[];  // ≤ 3, same language
}

interface Item { text: string; source_ids: string[] }               // e.g. ["S1", "S3"]
interface LawPoint { quote: string; explanation: string; source_ids: string[] }
```

Rules:

- `not_found` / `off_topic`: only `title`, `summary` and optionally `follow_up_questions`. Every other array is empty and the nullable fields are null.
- `source_ids` refer to the context labels `S1..Sn`. In `final`, unknown IDs are **removed**, and an item can end up with `source_ids: []`, which the UI shows without a citation badge.
- `office` is **not** part of `Answer`. Office data comes only from the database (`OfficeMatch`).
- The disclaimer is static UI text per language, not model output.

### Source

```ts
interface Source {
  id: string;                     // "S1" …, matches source_ids
  kind: "law" | "service_page" | "other";
  title: string;
  publisher: string;              // "lex.uz", "my.gov.uz"
  url: string;
  section: string | null;         // "14-modda" / "Article 14"
  published_at: string | null;    // YYYY-MM-DD
  fetched_at: string;             // ISO datetime
}
```

`sources` in `final` lists only the sources cited at least once, in order of first citation. The original `S` IDs are kept.

### Office

```ts
interface OfficeMatch {
  match: "district" | "region" | "none";   // "region": an approved office of this type elsewhere in the user's region (not the nearest; no distance is computed). "none": office type known, no office in the DB
  office_type: { code: string; label: string };
  office: Office | null;
}

interface Office {
  id: string;
  name: string;
  office_type: { code: string; label: string };
  address: string;
  district: { id: number; name: string };
  region: { id: number; name: string };
  phone: string | null;
  working_hours: WorkingHours[];          // empty = unknown
  latitude: number | null;
  longitude: number | null;
  map_url: string;                        // Google Maps URL from coordinates, else from address
  data_as_of: string;                     // YYYY-MM-DD
  source_url: string;
}

interface WorkingHours {
  days: ("mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun")[];
  open: string;                            // "09:00"
  close: string;                           // "18:00"
  break: { start: string; end: string } | null;
}
```

Localization: `office_type.label`, `district.name` and `region.name` come in the user's `ui_language`. `office.name` and `address` are shown **as stored**, in the source's language, and are never translated.

`map_url` takes one of two forms:
- with coordinates: `https://www.google.com/maps/search/?api=1&query=<lat>,<lng>`;
- without: `…&query=<url-encoded name + address>`.

Initial office type codes:
- `public_service_center`
- `migration`
- `civil_registry`
- `notary`
- `tax`
- `cadastre`
- `khokimiyat`
- `other`

The admin can add more.

---

## 6. Example `final` (illustrative values, not real facts)

The example values below are layout placeholders for design and mocks. Never present them as real information.

```json
{
  "message": {
    "id": "b34c…", "role": "assistant", "created_at": "2026-10-22T09:15:03Z", "status": "complete",
    "refused": false, "feedback": null,
    "answer": {
      "answer_type": "service",
      "language": "uz-Latn",
      "title": "Pasportni almashtirish",
      "summary": "Pasportni almashtirish uchun ariza topshirasiz va tayyor hujjatni olasiz.",
      "steps": [
        { "text": "Arizani onlayn yoki Davlat xizmatlari markazida topshiring.", "source_ids": ["S1"] },
        { "text": "Davlat bojini toʻlang.", "source_ids": ["S1"] },
        { "text": "Tayyor hujjatni markazdan oling.", "source_ids": ["S2"] }
      ],
      "documents": [
        { "text": "Eski pasport", "source_ids": ["S1"] },
        { "text": "Toʻlov kvitansiyasi", "source_ids": ["S1"] }
      ],
      "fee": { "text": "NAMUNA: bazaviy hisoblash miqdorining X foizi", "source_ids": ["S1"] },
      "processing_time": { "text": "NAMUNA: N ish kuni", "source_ids": ["S2"] },
      "law_points": [],
      "follow_up_questions": ["Pasportni onlayn almashtirsa boʻladimi?"]
    },
    "sources": [
      { "id": "S1", "kind": "service_page", "title": "NAMUNA xizmat sahifasi", "publisher": "my.gov.uz",
        "url": "https://my.gov.uz/", "section": null, "published_at": null, "fetched_at": "2026-10-20T08:00:00Z" },
      { "id": "S2", "kind": "law", "title": "NAMUNA nizom", "publisher": "lex.uz",
        "url": "https://lex.uz/", "section": "12-band", "published_at": "2024-01-01", "fetched_at": "2026-10-20T08:00:00Z" }
    ],
    "office": {
      "match": "district",
      "office_type": { "code": "public_service_center", "label": "Davlat xizmatlari markazi" },
      "office": {
        "id": "0d7e…", "name": "NAMUNA Chilonzor tumani Davlat xizmatlari markazi",
        "office_type": { "code": "public_service_center", "label": "Davlat xizmatlari markazi" },
        "address": "NAMUNA koʻchasi, 1-uy", "district": { "id": 1726269, "name": "Chilonzor tumani" },
        "region": { "id": 1726, "name": "Toshkent shahri" }, "phone": "+998 71 000 00 00",
        "working_hours": [
          { "days": ["mon","tue","wed","thu","fri"], "open": "09:00", "close": "18:00",
            "break": { "start": "13:00", "end": "14:00" } },
          { "days": ["sat"], "open": "09:00", "close": "13:00", "break": null }
        ],
        "latitude": null, "longitude": null,
        "map_url": "https://www.google.com/maps/search/?api=1&query=NAMUNA",
        "data_as_of": "2026-10-20", "source_url": "https://example.org/offices"
      }
    }
  }
}
```

---

*Contract v1.0, 2026-10-22: initial version.*
*Contract v1.1, 2026-10-22: added the change-password endpoint and `Me.has_password`; `POST /auth/resend-verification`; `GET /sources` + `SourceSummary`; assistant `error_code` (incl. `"stopped"`) and the Stop behaviour; `scope` on `quota_exceeded`; clarified `match: "region"`. These answer the design open questions in PR #1.*
*Contract v1.2, 2026-10-22: auth error codes table (`turnstile_failed` and the allauth/Django codes). Retry after Stop re-sends the question as a new user message, so history shows both attempts.*
*Contract v1.3, 2026-10-22: from backend findings on allauth 65.20. Removed `email_taken` (enumeration prevention: signup with an existing email looks like a new signup) and `password_too_similar` (never fires at signup). Added the `account_reset_password` → `/forgot-password` frontend URL and the decoded-key rule for email links.*
*Contract v1.4, 2026-10-22: from the frontend's cross-check of PR #3.
- Errors: `csrf_failed` and `permission_denied`; all `/api/` errors are problem+json; `retry_after` only on rate/quota errors.
- PATCH /me: changing the region requires a district.
- Districts endpoint returns 404 for an unknown region.
- Conversation `title` is never empty; `last_message_preview` = the last user message.
- `SourceSummary.last_fetched_at` is nullable.*
*Contract v1.5, 2026-10-22: office localization. Type, district and region labels follow `ui_language`; office name and address are shown as stored.*
