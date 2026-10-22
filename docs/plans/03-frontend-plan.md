# Frontend Plan: React SPA

**Lane:** Frontend. **Agent:** Madina (Claude). **Branch:** `feat/frontend-mvp` (own worktree).
**Inputs:**
- `/AGENTS.md`, `frontend/AGENTS.md`;
- `00-main-plan.md`;
- **`docs/contract.md`**;
- `docs/design/` (after gate G2).

**Owns:** `frontend/`, `.github/workflows/frontend.yml`.

**Order:**
1. F0–F1 start **now**, using mocks and unstyled components.
2. F2 starts **after G2** (design approved).
3. F3 starts **after G3** (backend MVP).

---

## 1. Stack

Use the latest stable version of each. Pin exact versions in `package-lock.json`.

| Concern | Choice |
|---|---|
| Runtime / build | Node 24 LTS (`node:24-alpine`), **Vite 8**, **React 19** |
| Language | **TypeScript 6.0**, `strict: true`. Not 7.x: typescript-eslint only supports TS < 6.1 today |
| Routing | React Router 8 (data router: `createBrowserRouter`, loaders for guards) |
| Server state | TanStack Query 5 |
| Forms | react-hook-form 7 + zod 4 |
| i18n | i18next + react-i18next. Locales `uz-Latn` (default), `uz-Cyrl`, `ru`, `en` |
| Styling | **Tailwind CSS 4**, with the theme taken **only** from `docs/design/tokens.css` (`@theme` maps the CSS variables). No raw hex or px values outside the tokens |
| Primitives | Native HTML first. Radix primitives only where native isn't enough (Dialog, Select/Combobox, DropdownMenu). Icons: `lucide-react` |
| Streaming | `fetch` + `ReadableStream` + `eventsource-parser`; `partial-json` for live answer parsing |
| Mocks | MSW 3 (browser + Node), handlers built from the contract examples |
| Testing | Vitest 5 + Testing Library + MSW; `@axe-core/playwright` + Playwright for E2E smoke and a11y |
| Lint / format | ESLint 10 + typescript-eslint 8 + `eslint-plugin-react-hooks` + `eslint-plugin-jsx-a11y` + **`eslint-plugin-jsdoc` (`require-jsdoc` on functions, arrow-function components, hooks, classes, methods)** + Prettier |
| Types | `openapi-typescript` → `src/api/generated/openapi.d.ts` from `docs/schema/openapi.json`; `json-schema-to-typescript` → `src/api/generated/answer.d.ts` from `docs/schema/answer.schema.json`. **Before G3**, write the types by hand in `src/api/types.ts`, copied exactly from `docs/contract.md` §3–§5, and replace them with the generated ones at F3 |

---

## 2. Structure

```
frontend/
├── src/
│   ├── main.tsx                     # bootstrap: i18n, QueryClient, MSW (if VITE_USE_MOCKS), router
│   ├── app/
│   │   ├── router.tsx               # routes + guards
│   │   ├── guards.ts                # requireAuth, requireVerified, requireProfile
│   │   └── layout/                  # AppShell (sidebar/drawer, top bar), AuthLayout
│   ├── api/
│   │   ├── http.ts                  # fetch wrapper: same-origin, CSRF header, problem+json → ApiError
│   │   ├── auth.ts                  # allauth headless calls (contract §2)
│   │   ├── endpoints.ts             # /me, /geo, /conversations, /feedback, /suggestions
│   │   ├── queries.ts               # TanStack Query hooks + query keys (single place)
│   │   ├── chatStream.ts            # POST /chat → typed SSE event async iterator
│   │   ├── types.ts                 # contract types (hand-written until F3)
│   │   └── generated/               # F3: generated types
│   ├── features/
│   │   ├── auth/                    # SignupPage, LoginPage, CheckEmailPage, VerifyEmailPage, Forgot/ResetPassword
│   │   ├── onboarding/              # OnboardingPage (language, region → district)
│   │   ├── chat/                    # ChatPage, useChatStream, MessageList, InputBar, ProgressLine, FeedbackBar
│   │   ├── answer/                  # AnswerView + Summary, StepsList, DocumentsChecklist, FactsRow,
│   │   │                            #   LawPoints, SourcesList, OfficeCard, Disclaimer, FollowUpChips
│   │   ├── history/                 # HistoryList (page on mobile, sidebar on desktop)
│   │   ├── settings/                # SettingsPage
│   │   └── about/                   # AboutPage
│   ├── components/ui/               # Button, TextField, PasswordField, Combobox, Chip, Badge, Alert, Dialog, Drawer, Skeleton, …
│   ├── i18n/
│   │   ├── index.ts
│   │   └── locales/{uz-Latn,uz-Cyrl,ru,en}.json
│   ├── lib/                         # openNow.ts (Asia/Tashkent), format.ts (dates, numbers), cn.ts
│   ├── mocks/                       # handlers.ts, browser.ts, server.ts, fixtures/ (from contract §6), sse.ts (mock stream)
│   └── styles/
│       ├── tokens.css               # copied unchanged from docs/design/tokens.css (sync script, never hand-edited)
│       └── index.css                # @import "tailwindcss"; @theme from tokens
├── e2e/                             # Playwright smoke + axe
├── nginx/default.conf
├── public/                          # favicon, self-hosted fonts
├── index.html  vite.config.ts  tsconfig.json  eslint.config.js  package.json
├── .env.example                     # VITE_USE_MOCKS, VITE_TURNSTILE_SITE_KEY
├── Dockerfile  .dockerignore
```

`npm run sync:tokens` copies `docs/design/tokens.css` into `src/styles/tokens.css`. CI fails if they differ (DRY: one source).

---

## 3. Routes and guards

| Route | Page | Guard |
|---|---|---|
| `/signup`, `/login`, `/forgot-password` | Auth | Guest only; redirect to `/` when logged in |
| `/check-email` | "Check your email" | Pending verification |
| `/verify-email/:key`, `/reset-password/:key` | Key flows | Public |
| `/onboarding` | Language + region/district | Auth + verified |
| `/` | New chat | Auth + verified + `profile_complete` |
| `/c/:conversationId` | Existing chat | Same |
| `/history` | History (mobile) | Same |
| `/settings`, `/about` | — | Auth (About also public) |
| `*` | 404 | — |

Boot sequence:
1. `GET /api/v1/csrf`.
2. `GET /_allauth/browser/v1/auth/session`.
3. If authenticated, `GET /api/v1/me`.
4. Apply the guards. A missing district sends the user to `/onboarding`.

The UI language comes from the profile (`ui_language`). Before login it is stored in `localStorage` (a convenience only). Update `<html lang>` on every change.

---

## 4. Chat streaming (`useChatStream`)

- `chatStream.ts`:
  - `POST /api/v1/chat` with `{conversation_id, text}`, `Accept: text/event-stream`, and the CSRF header;
  - an `AbortController` drives the **Stop** button;
  - `eventsource-parser` produces typed events `meta | status | office | delta | final | error | done`, and comment pings are ignored;
  - a non-2xx response before the stream starts throws the `ApiError` parsed from problem+json.
- The hook's state is `{ stage, office, partialAnswer, finalMessage, error, isStreaming }`.
  - On `delta`, append to a buffer and run `partial-json` `parse(buffer)`. **Throttle the parse/render to one per animation frame.**
  - On `final`, replace the partial answer with the validated message and invalidate the conversation queries.
  - On `error`, show an inline error with **Retry**, which resends the same text.
  - On `meta`, if this was a new chat, navigate to `/c/:conversationId` without remounting the stream.
- Only one stream at a time. Disable the input while streaming (the backend also returns 409).
- Accessibility:
  - the live region (`aria-live="polite"`) announces the stage changes and the **final** summary, not every delta;
  - focus stays in the input.

## 5. Answer rendering

`AnswerView` maps contract §5 to the design components, in schema order:

- **service:** title/summary → steps → documents → fee + processing time → (office card, from the `office` event / `final.office`) → law points (if any) → sources → disclaimer → feedback → follow-ups.
- **legal:** title/summary → law points (quote + explanation) → steps ("what you can do") → sources → disclaimer → feedback.
- **not_found / off_topic:** title/summary + follow-ups or suggestion chips.

Supporting rules:
- **Citation badges:** each `source_ids` entry becomes `[n]`, numbered by the position in `sources`. A badge jumps to its source and highlights it. Items with no valid sources show no badge.
- **OfficeCard:**
  - the `match` variants per the design;
  - `openNow(working_hours, now)` computed in `Asia/Tashkent` (unit-tested, including the lunch break and "opens at");
  - a `tel:` link;
  - the map button `href={map_url}` with `target="_blank" rel="noopener noreferrer"`;
  - "data as of" + the source link.
- **Plain text only.** Never use `dangerouslySetInnerHTML`, because answers are text fields, which makes XSS impossible by construction.
- While streaming, render only the fields present in the partial object, with skeletons for the expected next blocks, so the layout doesn't jump when `final` arrives.

## 6. Other features

- **Auth:**
  - zod schemas mirror the backend rules (email, password ≥ 10);
  - the Turnstile widget on signup (site key from `VITE_TURNSTILE_SITE_KEY`; Cloudflare's test key in dev);
  - "Continue with Google" posts the allauth provider-redirect form;
  - allauth error codes map to i18n messages.
- **Onboarding:** pick the language, then a searchable region combobox, then the district combobox loaded with `/geo/regions/{id}/districts`. Save with `PATCH /me`.
- **History:** cursor-paginated list (infinite scroll or a "Load more" button), delete with a confirm dialog, "New chat".
- **Settings:**
  - language and region/district (PATCH `/me`);
  - quota usage from `/me.quota`;
  - change password (allauth);
  - log out;
  - delete account (`DELETE /me` with a confirm dialog, then log out).
- **Feedback:** 👍/👎 with an optional comment, upserted via `POST /messages/{id}/feedback`; shows the saved state.
- **Errors:**
  - a global offline banner;
  - `rate_limited` / `quota_exceeded` messages using `retry_after`;
  - a 401 anywhere logs the user out and sends them to `/login`.

## 7. i18n

- Every user-facing string goes through `t()`. No hardcoded text (enforced by review, plus an ESLint rule if practical).
- `uz-Latn.json` and `en.json` come from `docs/design/copy.md`; `ru.json` is translated.
- **`uz-Cyrl.json` is generated from `uz-Latn.json`** by `scripts/translit-uz.ts`, using the same mapping rules as the backend's `common/text.py`, but in reverse. The generated output is committed and flagged for native review.
- Keys are namespaced by feature (`chat.input.placeholder`). A test checks that all 4 locale files have identical key sets.

## 8. Accessibility and performance

- WCAG 2.2 AA:
  - keyboard reachable;
  - visible focus;
  - labelled inputs and icon buttons;
  - targets ≥ 44 px;
  - works at 200% zoom and at 320 px width;
  - respects `prefers-reduced-motion`;
  - axe checks in E2E show no serious or critical violations.
- Performance:
  - route-level code splitting;
  - **initial JS ≤ 200 KB gzip** (checked in CI);
  - self-hosted fonts with `font-display: swap`;
  - no runtime CSS-in-JS;
  - Lighthouse mobile ≥ 90 for Performance and Accessibility on the chat page.

## 9. Security

- `credentials: "same-origin"`. CSRF header on every non-GET request. No tokens or PII in `localStorage`, apart from the pre-login language preference.
- No inline scripts or styles, so the SPA works under a strict CSP. nginx sends the SPA's CSP, which allows only `self` + `https://challenges.cloudflare.com` for Turnstile.
- External links use `rel="noopener noreferrer"`.
- Never log answer text or user input to the console in production builds.

## 10. Docker and nginx

**`frontend/Dockerfile`:**

| Stage | Contents |
|---|---|
| `build` | `node:24-alpine`: `npm ci` with a cache mount, then `npm run build` |
| `runtime` | `nginxinc/nginx-unprivileged:1.31-alpine`: copy `dist/` and `nginx/default.conf`. Listens on 8080, runs non-root, ≤ 60 MB |

**`nginx/default.conf`:**
- SPA fallback: `try_files $uri /index.html`.
- `/assets/` cached `immutable, max-age=31536000`; `index.html` sent with `no-cache`.
- gzip.
- Security headers: CSP, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`.
- `location /api/`, `/_allauth/`, `/static/` and the admin path (`ADMIN_URL`, templated through env) proxy to `backend:8000`.
- **For `/api/v1/chat`:** `proxy_buffering off; proxy_cache off; proxy_read_timeout 300s;` and HTTP/1.1 keep-alive.
- Real IP: `set_real_ip_from` the internal Docker network, `real_ip_header CF-Connecting-IP`, and forward `X-Forwarded-For` / `X-Forwarded-Proto`.

**Dev:** run `npm run dev` (Vite on 5173) with `server.proxy` for `/api`, `/_allauth`, `/static` and `/admin` → `http://localhost:8000`. With `VITE_USE_MOCKS=true`, MSW serves everything and no backend is needed.

The main session adds the `web` service to `compose.yaml` at G4. Do not edit the compose files.

**CI** (`.github/workflows/frontend.yml`, on `frontend/**`, `docs/design/tokens.css`):
1. `npm ci`;
2. lint;
3. typecheck;
4. `vitest run --coverage`;
5. tokens-sync check;
6. locale key check;
7. build + bundle-size check;
8. Playwright smoke against `vite preview` with MSW;
9. docker build + size check (≤ 60 MB) + Trivy.

---

## 11. Phases and acceptance

| Phase | Scope | Done when |
|---|---|---|
| **F0** Scaffold | Vite + React + TS strict, ESLint (with jsdoc), Prettier, Vitest, MSW, router + guards, i18n with 4 locale files, `http.ts` (CSRF, problem+json), contract types, Dockerfile + nginx, CI | `npm run lint && npm run typecheck && npm test && npm run build` pass. The app boots against mocks |
| **F1** Logic on mocks | Auth flows, onboarding, chat with a **mock SSE stream** (MSW emits the contract §4 events with the §6 fixture, fragmenting the JSON), history, settings, feedback, errors. Unstyled or minimal styling | The whole user journey works on mocks. Unit tests cover `chatStream`, `useChatStream`, `openNow`, citation numbering, guards and the locale keys |
| **F2** Apply design (after **G2**) | Sync the tokens, build the `components/ui` + answer components exactly to `docs/design/components.md` / `screens.md` / the prototype, at every breakpoint and in every state | Visual check against `docs/design/screenshots/` at 375 and 1440; axe shows no serious issues |
| **F3** Real backend (after **G3**) | Switch off the mocks, generate the types from `docs/schema/`, fix the mismatches (report contract issues), add E2E against the local stack | Signup → verify (console email link) → onboarding → passport question streams into cards with sources (+ office card when data exists) → feedback saved |
| **F4** Polish | a11y, performance budgets, empty/error states, translations reviewed, docs | All §8 targets met, PR ready |

---

## 12. Prompt for the frontend session

```text
You are Madina (Claude), the frontend engineer for GovAssist, an MSc thesis project: a RAG-based web assistant that
answers questions about public services and laws of Uzbekistan with clean, step-by-step answer cards, sources and
the exact office in the user's district.

Work only in a git worktree on branch `feat/frontend-mvp`. You own: frontend/ and .github/workflows/frontend.yml.
Do not edit backend/, compose files, tasks.py, docs/contract.md, docs/plans/ or docs/design/.

Read first, fully:
1. /AGENTS.md and frontend/AGENTS.md (rules: clean code, DRY, SOLID, TSDoc on every function, component, hook and class)
2. docs/plans/00-main-plan.md (product and fixed decisions)
3. docs/contract.md (API, auth endpoints, SSE events, Answer schema, example payloads)
4. docs/plans/03-frontend-plan.md (your plan; follow it section by section)

Do phases F0 and F1 from 03-frontend-plan.md §11 now, against MSW mocks built from docs/contract.md §4–§6.
Start F2 only when docs/design/README.md on main says "Status: Approved" (gate G2). Use docs/design/tokens.css as
the only source of design values (sync script, no raw hex). Start F3 only when the backend MVP PR is merged (gate G3).
Commit after each phase (Conventional Commits, e.g. "feat(chat): stream answer cards").

Hard rules:
- React 19, Vite 8, TypeScript 6.0 strict (not 7.x), React Router, TanStack Query, react-hook-form + zod,
  react-i18next (uz-Latn default, uz-Cyrl, ru, en), Tailwind CSS 4 themed from tokens.css,
  fetch + eventsource-parser + partial-json for streaming.
- Same-origin requests with the CSRF header; never store tokens or PII in localStorage.
- Render answer text as plain text only; never use dangerouslySetInnerHTML.
- Every user-facing string goes through i18n; the 4 locale files must have identical keys.
- WCAG 2.2 AA, phone-first, initial JS ≤ 200 KB gzip, Docker runtime image ≤ 60 MB, non-root nginx.
- If the contract is missing something or is wrong, do not work around it silently: note it in the PR under
  "Contract change request".
- Never invent real-looking fees, addresses or phone numbers in mocks; keep the NAMUNA/SAMPLE markers.

Done for this PR when:
- `npm run lint && npm run typecheck && npm test && npm run build` pass, CI is green.
- The full journey works on mocks: signup → check email → verify → onboarding → chat with live-streaming
  cards and stop/retry → history → settings → feedback.
- After G2: screens match docs/design at 375 and 1440 px. After G3: the same journey works against the real backend.

Then push and open a PR to main titled "Frontend MVP" with: what was built, how to run it (mocks and real backend),
the acceptance checklist, screenshots, deviations and open questions. Report back with the PR link and a short summary.
```
