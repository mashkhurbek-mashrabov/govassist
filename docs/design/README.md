# GovAssist design system v1.1

**Status: In review** (v1.1: Lucide icons, glass, UX polish). v1 was approved at gate G2 on 2026-10-22 (PR #1). See `docs/plans/00-main-plan.md` §5. **Lane:** Design, Sevara (Claude). **Plan:** [`01-design-plan.md`](../plans/01-design-plan.md). **Contract:** v1.5.

A calm, phone-first, WCAG 2.2 AA design for GovAssist: landing, auth, onboarding, chat with live-streaming answer cards, the office card, history, settings and about, plus **six clickable end-to-end journeys (J1–J6)**. It is deliberately **not** styled like a government site: warm neutral greys with one indigo accent, a plain wordmark, no emblem and no flag colours. "Rasmiy davlat xizmati emas" (*Not an official government service*) and the answer disclaimer are on every relevant screen.

## Files

| File | What it is |
|---|---|
| [`design-system.md`](design-system.md) | Principles, typography and glyph check, colour and **contrast table**, spacing, radius, elevation, motion (+ reduced motion), icons, accessibility rules |
| [`tokens.css`](tokens.css) | **The single source of design values** (CSS custom properties). The frontend copies it unchanged (`npm run sync:tokens`) |
| [`tokens.json`](tokens.json) | The same tokens in W3C Design Tokens format. Generated from `tokens.css`; never edit it by hand |
| [`tokens.mjs`](tokens.mjs) | `node docs/design/tokens.mjs` rewrites `tokens.json`; `--check` fails if it is stale, or if the prototype uses a raw hex/rgb colour, a raw rem/px length or an undefined variable |
| [`components.md`](components.md) | Every component: anatomy, variants, states, tokens, a11y; OfficeCard rules; streaming behaviour; journey playback |
| [`screens.md`](screens.md) | All 17 screens (0–16): purpose, layout per breakpoint, components, states, copy keys, contract fields; then the journeys table |
| [`copy.md`](copy.md) | UI strings in uz-Latn + en with length budgets, plus the **error code → copy key** map (contract §1, §2, §4) |
| [`icons/`](icons/) | The 40 Lucide icons used, copied unchanged from `lucide-static` 1.61.0, plus the ISC licence. `tokens.mjs --check` fails if an inline icon differs from these files |
| [`fonts/`](fonts/) | Inter 5.3.0, 400 + 600, latin / latin-ext / cyrillic / cyrillic-ext WOFF2, `inter.css`, OFL licence |
| [`prototype/index.html`](prototype/index.html) | Every screen and state: one file per screen with a state bar, plus `components.html` and `type.html` (glyphs + long-string test) |
| [`prototype/journeys.html`](prototype/journeys.html) | Start page for **J1–J6**; each journey is one file (`j1.html` … `j6.html`), 91 linked steps in total |
| [`prototype/flow.js`](prototype/flow.js) | The one shared script: step navigation, form submits, timed streaming playback (Pause; text jumps under reduced motion), `?shot` mode for screenshots |
| [`screenshots/`](screenshots/) | 164 PNGs (82 states × 375×812 and 1440×900) + `glyph-proof.png` |
| [`screenshots/journeys/`](screenshots/journeys/) | Every journey step in order at 375×812 (`J1-01-landing.png` …), J2 and J6 also at 1440×900: 118 PNGs |
| [`screenshots/glass/`](screenshots/glass/) | Glass chrome over scrolled content, each next to its two solid fallbacks (`prefers-reduced-transparency` and no `backdrop-filter`): 15 PNGs |
| [`shoot.cjs`](shoot.cjs) | Playwright script that makes all screenshots and runs the audits below |
| **Design canvas** | [claude.ai/artifact/HUejpbC6LwuZPH67qn8EwM](https://claude.ai/artifact/HUejpbC6LwuZPH67qn8EwM): 45 artboards, one row per journey (J1, J2, J3, J4, J5, J6, J6 part 2, other screens) with a title note each; phone boards 390 wide, chat/history/settings boards 1440 wide for J2 and J6. Primary buttons are prototype links between artboards; streaming boards play their stages by themselves (Replay). The canvas is private until shared from its Share menu |

## How to use it

- **Click through a journey:** open `prototype/journeys.html` from disk and press Start. The dashed bar at the top shows the step, with Back, **Pause** and Next. No build, no server, no network.
- **Look at one screen or state:** open `prototype/index.html`; each page's dashed state bar switches states (also `#state` in the URL).
- **Check tokens:** `node docs/design/tokens.mjs --check` → `tokens OK, prototype OK`.
- **Re-make screenshots and run the audits:** see the header of `shoot.cjs` (`npm i playwright axe-core` in a scratch folder, then `node docs/design/shoot.cjs`).

**Last audit run** (`shoot.cjs`, all pages and journeys): `screenshots written, audits clean`. That means: no horizontal overflow at 375 px; no interactive target under 44 px at either size; axe-core WCAG 2.0/2.1/2.2 A + AA rules show 0 serious or critical issues on every state and every journey step (this includes colour contrast); every in-journey link points to an existing step and every step but the last has a way forward; J1's streaming plays from "searching" to the final answer by itself, with and without reduced motion.

Notes for reviewers:
- Screenshots use `prefers-reduced-motion: reduce`, so they show the reduced-motion variant (static dots, flat skeletons, full text).
- In full-page shots the sticky InputBar and the desktop sidebar are unstuck so they appear once, in place. States with a drawer, dialog or toast are captured at viewport size.
- Each gallery file renders all its states and shows one at a time, so some IDs repeat inside hidden states. In React each state is a separate render.
- Content is the illustrative data from `docs/contract.md` §6. Everything the journeys add (the legal, Russian, off-topic, not-found, birth-certificate and driving-licence answers, extra offices and sources) is marked `NAMUNA` / `SAMPLE`. No fees, addresses, phone numbers or law articles were invented.
- Journey steps the app can't show by itself (an email arriving, a page reload, moving to the next limit state) carry a dashed **Prototype** note with a link.

## v1.1: before → after

The author asked for "one icon package, not similar, glass effect, better UI/UX" and then "make prettier, use a little bit gradient, make as professional" (`01-design-plan.md` §3, v1.1).

| Area | v1 (before) | v1.1 (after) |
|---|---|---|
| Icons | Lucide-style paths drawn by hand from memory (close, not exact) | Exact `lucide-static` 1.61.0 SVGs copied into `icons/`; `tokens.mjs --check` rejects any other icon; inventory with `lucide-react` names in `components.md` |
| Chrome | Solid white top bar, sidebar and drawer; composer on the page colour | Frosted glass on the top bar, composer, sidebar, drawer, dialogs and toasts (tokens: alpha, blur 14 px, saturate, border, highlight, shadow); solid fallbacks for no `backdrop-filter` and `prefers-reduced-transparency` |
| Page backdrop | Flat `#FAFAF9` | Soft indigo/amber radial washes on a fixed layer, so the glass reads; text still ≥ 6:1 on the darkest point |
| Answer hierarchy | Small grey kind label; h2 title the same size as section titles | Kind shown as a primary pill; title at h1 size; summary in full-strength body-lg, so title + summary are read first |
| Section headers | Small inline icon + h3 | Icon in a 36 px primary-subtle tile + h3, 12 px gap: easier to scan |
| Steps | Pale numbered circles | Filled primary circles with white numbers (7.31:1) |
| Cards and spacing | 16 px padding, 16 px between cards, flat | 20/24 px padding, 20 px between cards, 32 px between messages, `--shadow-1` lift; desktop pages get 40 px top space |
| Radius | 6 / 10 / 16 px | 8 / 12 / 20 px: softer, friendlier |
| Primary actions | Flat indigo buttons | Indigo glow (`--shadow-primary`) on primary buttons and Send; the main action stands out on every screen |
| Micro-interactions | Colour change on hover only | Press scale (0.98) on buttons, chips and icon buttons; chips lift 2 px on hover; answer blocks fade and rise in as they stream; all off under reduced motion |
| Empty, loading, error | Plain icon circle; flat chips | Empty/success/error icons sit in a ringed circle; chips and the InputBar have a soft lift; loading keeps the skeletons; error alerts unchanged in copy and roles |
| Overall look | Plain, flat, one solid indigo | A premium SaaS feel with restrained gradients (indigo → violet, low contrast): brand gradient on primary buttons, Send, logo mark and step numbers; gradient hero panels and gradient headline text on the landing and chat greeting; soft gradient for active/selected states and the user bubble; violet-tinted wash behind the glass |
| Depth | Two simple shadows, grey card borders | Three-layer shadows, a softer 7 % card edge, a white → stone-50 card surface, a brand-gradient edge on the office card, a violet glow under primary actions |
| Screenshots | 25 MB | Palette PNG (256 colours, dithered) via `shoot.cjs`: 18 MB for more shots |

## Review checklist (`01-design-plan.md` §8)

- [x] Every screen and state in §4 is present in `screens.md`, the prototype and the screenshots. *(17 screens incl. the landing, 82 states, 164 state screenshots.)*
- [x] All answer types (service, legal, not_found, off_topic), every office variant (district, region, none, no office, unknown hours/phone) and the streaming stages (searching → found → office early → summary → steps → documents → fee/time → final, plus stopped) are designed.
- [x] Data shown matches `docs/contract.md` field by field, and nothing needs data the API doesn't provide. *(Field mapping per screen in `screens.md`; v1.1/v1.2 additions used: `has_password`, resend-verification, `/sources`, `error_code`, `scope`, auth error codes, retry keeps both attempts.)*
- [x] Contrast table passes AA, targets ≥ 44 px, focus states visible, reduced-motion variant defined. *(`design-system.md` §3 and §7; audits above.)*
- [x] 375 px layouts don't overflow with long Russian/Cyrillic strings. A test string set is included. *(`prototype/type.html`, J2 (uz-Cyrl), J3 and J6 (ru); no overflow found.)*
- [x] The font renders oʻ gʻ (U+02BB) and ў қ ғ ҳ correctly. Screenshot proof included. *(`screenshots/glyph-proof.png`.)*
- [x] `tokens.css` and `tokens.json` agree and cover every value used in the prototype (no raw hex in the prototype CSS). *(`tokens.mjs --check`.)*
- [x] No official-government imitation. The disclaimer and the "not official" note are present.
- [x] No invented real facts. Sample markers kept.
- [x] The prototype opens offline with no build step.
- [x] **J1–J6 are clickable end to end**, in both the prototype and the design canvas. No dead ends: every primary action leads somewhere. *(Prototype: checked by `shoot.cjs`. Canvas: every board links onward; the last board of each journey links to the next journey.)*
- [x] The landing page exists. J1 includes a second turn in the same thread. J2 shows a full legal answer. J3 shows a Russian answer.
- [x] Streaming plays by itself in the journeys, with a reduced-motion variant. *(`flow.js` timers + Pause; under reduced motion the text appears at once. Canvas streaming boards play on their own.)*
- [x] `screenshots/journeys/` has every step of every journey. *(91 steps at 375; J2 and J6 also at 1440.)*
- [x] (v1.1) Every icon is a real Lucide icon from one pinned `lucide-static` version, and the inventory is in `components.md`. *(1.61.0; 40 icons in `icons/`; enforced by `tokens.mjs --check`, which also caught the old hand-drawn menu icon in a negative test.)*
- [x] (v1.1) Glass is on the listed chrome only, AA passes on glass, and the solid fallbacks for no-`backdrop-filter` and reduced transparency are designed and screenshotted. *(`design-system.md` §8a worst-case contrast table; `screenshots/glass/`.)*
- [x] (v1.1) A UX polish pass is done, with a before/after list in the README. *(Above. Includes the "prettier, a little gradient, professional" round: restrained indigo → violet gradient tokens with AA on every stop, `design-system.md` §8b.)*

## Open questions

Contract v1.1 and v1.2 answered all six questions from the first review:

| # | Question | Answer used in the design |
|---|---|---|
| 1 | Resend verification / change email | `POST /api/v1/auth/resend-verification` (always 204; 429 + `retry_after`); "use another email" goes to `/signup` |
| 2 | Change password | allauth `account/password/change`; current password hidden when `Me.has_password` is false ("Parol oʻrnatish") |
| 3 | What Stop stores | `status: failed`, `error_code: "stopped"`, no partial answer; Retry re-sends, so the thread keeps both attempts (J5) |
| 4 | About source list | `GET /api/v1/sources` → `SourceSummary` |
| 5 | Two kinds of `quota_exceeded` | `scope: user` vs `scope: global`, with separate copy |
| 6 | Region fallback wording | "another office in your region" (`hududingizdagi boshqa idora`) |

Contract v1.5 answered the last one: `office_type.label` and the district and region names follow `ui_language`; office `name` and `address` are shown as stored. The design already does this (the Russian UI in J6 shows localized region/district names).

No open questions.

## Deviations and limits

- **Tabs** are optional in the plan and no screen needs them, so they are not designed.
- **Dark theme** tokens exist (`data-theme="dark"`) and pass contrast, but no screen was reviewed in dark mode; treat it as provisional.
- **ru and uz-Cyrl copy** is out of scope (`copy.md` is uz-Latn + en per plan §6). The Russian UI strings in J6, `welcome.html#ru` and `settings.html#ru`, and the Cyrillic strings in `type.html`, are layout and journey strings, not reviewed translations.
- Answer content follows the question's script (`answer.language`) while the UI follows `ui_language`, so J2 (uz-Cyrl) and J3 (ru) mix a Latin UI with Cyrillic content. Only J6 switches the UI language itself.
- The canvas boards are hand-written mirrors of the prototype: same tokens and stylesheet, simplified markup, fewer icons. The prototype in this folder is the markup reference for React.
- Desktop screenshots are 1440×900 as requested; the plan's 1280 breakpoint is where the sidebar appears, so 1280–1440 share one layout.
- The Turnstile widget is a 300×65 SAMPLE placeholder; Cloudflare renders the real one.
