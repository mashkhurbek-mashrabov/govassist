# GovAssist frontend

React 19 + Vite 8 + TypeScript 6.0 SPA. Rules: [`AGENTS.md`](AGENTS.md). Plan: [`docs/plans/03-frontend-plan.md`](../docs/plans/03-frontend-plan.md). API: [`docs/contract.md`](../docs/contract.md).

Status: complete against contract **v1.10** and design **v1.3**: real backend, streaming answer cards, four languages, account menu. Mock mode (below) still runs without a backend.

## Run

```bash
npm ci
npm run dev:mock   # http://localhost:5173, every API call served by MSW, no backend needed
npm run dev        # http://localhost:5173, proxies /api, /_allauth, /static, /admin to http://localhost:8000
```

### Mock mode

- Seeded accounts: `namuna@example.com` (has a password) and `google-namuna@example.com` (Google-only, `has_password: false`, to try "set a password"). Any password works; the mock rejects only `wrong-password`.
- Signed-out visitors land on `/welcome`.
- Signup and password-reset links are printed to the browser console as `[MSW mail] …`, like Django's console email backend. Open the link in the same tab: the mock state survives reloads (sessionStorage, mock mode only). "Resend" on the check-email page is rate-limited to once a minute.
- Stop stores the answer as `failed` / `error_code: "stopped"`, so a reload shows "Answer stopped" with Retry.
- Question triggers: `#limit` → 429 `rate_limited` (retry in 21 min), `#quota` → 429 `quota_exceeded` (scope `user`), `#globalquota` → 429 `quota_exceeded` (scope `global`), `#busy` → 409 `stream_in_progress`, `#error` → in-stream `error` event, `#offtopic` → off-topic answer.
- All mock data comes from contract §3/§6 and keeps the `NAMUNA` / `SAMPLE` markers. Nothing is real.

## Checks

| Command                                        | What                                                                  |
| ---------------------------------------------- | --------------------------------------------------------------------- |
| `npm run lint`                                 | ESLint (strict TS, hooks, jsx-a11y, `require-jsdoc`) + Prettier       |
| `npm run typecheck`                            | `tsc --noEmit`, strict                                                |
| `npm test` / `npm run coverage`                | Vitest + Testing Library + MSW                                        |
| `npm run build` then `npm run check:size`      | Production build; initial JS ≤ 200 KB gzip                            |
| `npm run e2e`                                  | Playwright journey + axe on the mock build, at 375 and 1440 px        |
| `npm run check:tokens` / `npm run sync:tokens` | `src/styles/tokens.css` vs `docs/design/tokens.css` (no-op before G2) |
| `npm run check:i18n` / `npm run i18n:cyrl`     | `uz-Cyrl.json` is generated from `uz-Latn.json` (needs native review) |

E2E needs Chromium: `npx playwright install chromium`, or point `PLAYWRIGHT_CHROMIUM_PATH` at an existing Chromium binary. `E2E_BASE_URL=http://localhost:8080 npm run e2e` runs against an already-running server (for example the Docker image serving `dist-mock/`).

## Docker

```bash
docker build -t govassist-web .
docker run -p 8080:8080 -e BACKEND_HOST=backend:8000 -e ADMIN_URL=admin/ govassist-web
```

`nginxinc/nginx-unprivileged:1.31-alpine-slim`, non-root, port 8080, about 31 MB. nginx serves the SPA with a strict CSP, proxies `/api/`, `/_allauth/`, `/static/` and `/${ADMIN_URL}` to `${BACKEND_HOST}`, and turns buffering off for the SSE stream. Config: [`nginx/default.conf.template`](nginx/default.conf.template).
