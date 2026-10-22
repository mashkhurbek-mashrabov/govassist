# GovAssist design system v1

**Status: In review** (gate G2, `docs/plans/00-main-plan.md` §5). **Lane:** Design, Sevara (Claude). **Plan:** [`01-design-plan.md`](../plans/01-design-plan.md).

A calm, phone-first, WCAG 2.2 AA design for GovAssist: auth, onboarding, chat with live-streaming answer cards, the office card, history, settings and about. It is deliberately **not** styled like a government site: warm neutral greys with one indigo accent, a plain wordmark, no emblem and no flag colours. "Rasmiy davlat xizmati emas" (*Not an official government service*) and the answer disclaimer are on every relevant screen.

## Files

| File | What it is |
|---|---|
| [`design-system.md`](design-system.md) | Principles, typography and glyph check, colour and **contrast table**, spacing, radius, elevation, motion (+ reduced motion), icons, accessibility rules |
| [`tokens.css`](tokens.css) | **The single source of design values** (CSS custom properties). The frontend copies it unchanged (`npm run sync:tokens`) |
| [`tokens.json`](tokens.json) | The same tokens in W3C Design Tokens format. Generated from `tokens.css`; never edit it by hand |
| [`tokens.mjs`](tokens.mjs) | `node docs/design/tokens.mjs` rewrites `tokens.json`; `--check` fails if it is stale, or if the prototype uses a raw hex/rgb colour, a raw rem/px length or an undefined variable |
| [`components.md`](components.md) | Every component: anatomy, variants, states, tokens, a11y; OfficeCard rules; streaming behaviour |
| [`screens.md`](screens.md) | All 16 screens: purpose, layout per breakpoint, components, states, copy keys, contract fields |
| [`copy.md`](copy.md) | UI strings in uz-Latn + en with length budgets (source for `uz-Latn.json` / `en.json`) |
| [`fonts/`](fonts/) | Inter 5.3.0, 400 + 600, latin / latin-ext / cyrillic / cyrillic-ext WOFF2, `inter.css`, OFL licence |
| [`prototype/`](prototype/index.html) | Static HTML + CSS prototype, one file per screen, plus `components.html` and `type.html` (glyphs + long-string test) |
| [`screenshots/`](screenshots/) | 140 PNGs (70 states × 375×812 and 1440×900) + `glyph-proof.png` |
| [`shoot.cjs`](shoot.cjs) | Playwright script that makes the screenshots and runs the overflow / 44 px target / axe audits |

## How to use it

- **Open the prototype:** open `prototype/index.html` in a browser, straight from disk. No build, no server, no network (fonts are local). Each page has a dashed state bar at the top; the state is also in the URL hash (`answer-service.html#region`).
- **Check tokens:** `node docs/design/tokens.mjs --check` → `tokens OK, prototype OK`.
- **Re-make the screenshots:** see the header of `shoot.cjs` (`npm i playwright axe-core` in a scratch folder, then `node docs/design/shoot.cjs`).

Notes for reviewers:
- Screenshots use `prefers-reduced-motion: reduce`, so they show the reduced-motion variant (static dots, flat skeletons).
- In full-page shots the sticky InputBar and the desktop sidebar are unstuck so they appear once, in place. States with a drawer, dialog or toast are captured at viewport size.
- Each prototype file renders all its states and shows one at a time, so some IDs repeat inside hidden states. In React each state is a separate render.
- All content is the illustrative data from `docs/contract.md` §6. Anything else is marked `NAMUNA` / `SAMPLE`. No fees, addresses or phone numbers were invented.

## Review checklist (`01-design-plan.md` §8)

- [x] Every screen and state in §4 is present in `screens.md`, the prototype and the screenshots. *(16 screens, 70 states, 140 screenshots.)*
- [x] All answer types (service, legal, not_found, off_topic), every office variant (district, region, none, no office, unknown hours/phone) and the streaming stages (searching → found → office early → summary → steps → documents → final, plus stopped) are designed.
- [x] Data shown matches `docs/contract.md` field by field, and nothing needs data the API doesn't provide. *(Field mapping per screen in `screens.md`. The four places where a screen needs more than the contract gives are open questions 1–4 below; they are drawn as flows, not invented fields.)*
- [x] Contrast table passes AA, targets ≥ 44 px, focus states visible, reduced-motion variant defined. *(Contrast: `design-system.md` §3, light + provisional dark. Targets: measured on every screen at both sizes, none under 44 px. axe-core WCAG 2.2 AA: 0 serious/critical.)*
- [x] 375 px layouts don't overflow with long Russian/Cyrillic strings. A test string set is included. *(`prototype/type.html`; the script found no horizontal overflow on any screen.)*
- [x] The font renders oʻ gʻ (U+02BB) and ў қ ғ ҳ correctly. Screenshot proof included. *(`screenshots/glyph-proof.png`; `document.fonts.check` true for both sets.)*
- [x] `tokens.css` and `tokens.json` agree and cover every value used in the prototype (no raw hex in the prototype CSS). *(`tokens.mjs --check`.)*
- [x] No official-government imitation. The disclaimer and the "not official" note are present.
- [x] No invented real facts. Sample markers kept.
- [x] The prototype opens offline with no build step.

## Open questions (contract gaps, not designed around)

1. **Resend verification email / change email** (screens 3, 4). Contract §2 lists no allauth endpoint for resending the verification email or changing the email of an unverified account. The design has "Havolani qayta yuborish" (with a rate-limited state) and "Boshqa elektron pochtadan foydalanish" (currently back to `/signup`). Please add the allauth endpoints to §2, or say to drop the buttons. Also: does the resend limit return a wait time the UI can show?
2. **Change password** (screen 14). There is no change-password endpoint in §2, and `Me` does not say whether the account has a password (Google-only accounts don't). The design shows "Parolni oʻzgartirish", but it needs the endpoint plus a flag such as `has_password` (or the auth providers) to hide it for Google users.
3. **Stopped answers** (screen 8). When the user presses Stop, what is stored: `status: "failed"`, a partial answer, or nothing? The design keeps the partial cards on screen with "Javob toʻxtatildi"; history after a reload depends on the answer.
4. **About → source list** (screen 15). No endpoint returns the corpus sources (publisher, title, count, date). The design shows NAMUNA rows. Options: a public `GET /api/v1/sources`, or a static list built from `docs/corpus-sources.md`.
5. **`quota_exceeded` has two causes** (screen 12): the user's daily limit and the global daily token cap. The copy ("Ask again tomorrow") fits both, but a distinct `code` or `detail` would let the UI say "the service has reached today's limit" for the global case.
6. **Region fallback wording.** The plan says "nearest in your region", but `match: "region"` only means "an office in your region"; no distance is computed. The copy says "hududingizdagi boshqa idora". Change it if the backend does pick the nearest one.

## Deviations and limits

- **Tabs** are optional in the plan and no screen needs them, so they are not designed.
- **Dark theme** tokens exist (`data-theme="dark"`) and pass contrast, but no screen was reviewed in dark mode; treat it as provisional.
- **ru and uz-Cyrl copy** is out of scope (`copy.md` is uz-Latn + en per plan §6). The Russian and Cyrillic strings in `type.html` are layout test strings, not reviewed translations.
- Desktop screenshots are 1440×900 as requested in the brief; the plan's 1280 breakpoint is where the sidebar appears, so 1280–1440 share one layout.
- The Turnstile widget is a 300×65 SAMPLE placeholder; Cloudflare renders the real one.
