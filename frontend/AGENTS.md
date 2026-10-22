# AGENTS.md: frontend (React)

Extends `/AGENTS.md`. Full plan: `docs/plans/03-frontend-plan.md`.

## Stack

| Concern | Choice |
|---|---|
| Core | React 19, Vite 8, TypeScript 6.0 `strict` (not 7.x) |
| Routing / state / forms | React Router (data router), TanStack Query, react-hook-form + zod |
| i18n / styling | react-i18next, Tailwind CSS 4 themed from `src/styles/tokens.css` |
| Streaming | `eventsource-parser` + `partial-json` |
| Tests | MSW, Vitest + Testing Library, Playwright + axe |

## Rules

- **TSDoc on every function, component, hook, class and method.** `eslint-plugin-jsdoc` (`require-jsdoc`) enforces it.
- **Components:**
  - function components only, one per file, named exports;
  - props typed with an `interface`;
  - no logic-heavy JSX: move logic into hooks or `lib/`.
- **State:**
  - server state lives in TanStack Query only, with query keys defined once in `src/api/queries.ts`;
  - local UI state uses `useState`/`useReducer`;
  - no global store unless a real need appears.
- **API:**
  - everything goes through `src/api/http.ts` (same-origin, CSRF header, problem+json → `ApiError`);
  - types come from `src/api/types.ts`, later replaced by the generated ones;
  - never call `fetch` directly from components.
- **Styling:**
  - Tailwind utilities backed by design tokens only;
  - no raw hex or px values outside `tokens.css`, no inline `style` except computed values;
  - `tokens.css` is synced from `docs/design/tokens.css` and is never edited here.
- **i18n:**
  - every user-facing string goes through `t()`;
  - the 4 locale files keep identical keys;
  - `uz-Cyrl.json` is generated from `uz-Latn.json`, never hand-edited.
- **Security:**
  - render model output as plain text: **never `dangerouslySetInnerHTML`**;
  - no tokens or PII in `localStorage`;
  - external links use `rel="noopener noreferrer"`.
- **Accessibility:**
  - semantic HTML first;
  - labelled controls, visible focus, targets ≥ 44 px;
  - `aria-live` only for stage changes and final answers;
  - respect `prefers-reduced-motion`.
- **Tests:**
  - Testing Library queries by role/label, not test IDs, where possible;
  - MSW for network;
  - every hook and `lib/` function has unit tests.

## Commands

`npm run dev` (with `VITE_USE_MOCKS=true` for mocks) · `npm run lint` · `npm run typecheck` · `npm test` · `npm run build` · `npm run sync:tokens` · `npm run e2e`
