# Design Plan: Design System and Screens

**Lane:** Design. **Agent:** Sevara (Claude). **Branch:** `design/system-v1`. **Worktree:** `.claude/worktree/design`.
**Reviewer / approver:** main session (gate G2 in `00-main-plan.md`).
**Inputs:** `00-main-plan.md`, `docs/contract.md` (the data every screen shows), `/AGENTS.md`.
**Output folder:** `docs/design/` only.

---

## 1. Users and context

- Citizens of Uzbekistan of **all ages, including elderly and low-literacy users**, who are not technical.
- **Mostly phones:** mid/low-end Android, small screens, slow or unstable mobile internet. Desktop is secondary.
- Four languages:
  - **Uzbek Latin (default)**, with the apostrophe letters oʻ gʻ (U+02BB);
  - Uzbek Cyrillic (ў қ ғ ҳ);
  - Russian;
  - English.
- Russian and Cyrillic strings run 20–40% longer, so layouts must not break.
- Goal: find out *what to do, which documents to bring, what it costs, and exactly which office to visit*, without going to the wrong office.

## 2. Design principles

1. **Clarity over decoration.** One primary action per screen, plain words, short lines.
2. **Trust is visible.** Every fact can show its source, every office card shows "data as of <date>", and a disclaimer is always present.
3. **Calm and neutral.** It must **not imitate an official government site**:
   - no state emblem, flag-based branding or my.gov.uz look-alike;
   - show "Not an official government service" in the footer and on the About page;
   - the brand is a simple "GovAssist" wordmark.
4. **Accessible by default:** WCAG 2.2 AA.
   - Contrast ≥ 4.5:1 for text and ≥ 3:1 for UI elements.
   - Touch targets ≥ 44×44 px.
   - Body text ≥ 16 px.
   - Visible focus.
   - Works at 200% zoom.
   - Respects `prefers-reduced-motion`.
5. **Phone-first.** Design at 375 px first, then 768 and 1280+.
6. **Fast.** System-friendly visuals, no heavy imagery, at most 2 font weights per family, self-hosted fonts.

## 3. Brand and visual foundations

- **Typography:** one sans family with full Latin Extended (including U+02BB) and Cyrillic (including Uzbek letters). Candidates: Inter or Noto Sans. Verify the glyphs.
  - Type scale (mobile/desktop): display, h1, h2, h3, body-lg, body, small, caption.
  - Line height ≥ 1.5 for body text.
- **Color:**
  - A neutral base with one primary accent: calm and trustworthy, not flag colors.
  - Semantic colors: success, warning, danger, info.
  - "Open now" / "Closed" states.
  - Light theme required. Dark-theme tokens optional, but the token structure must support them.
- **Spacing:** a 4 px base scale.
- **Radius:** 3 steps. **Elevation:** 2 levels. **Motion:** durations and easing, plus a reduced-motion variant.
- **Icons: exactly one package, Lucide.** Use the **real** Lucide icons: exact SVGs copied from the `lucide-static` package at one pinned version, recorded in `design-system.md`. No hand-drawn look-alikes, no mixing with other sets. Keep an icon inventory in `components.md` (icon name → where used), so the frontend uses the same names from `lucide-react` at the same version. The only non-Lucide mark is the Google "G" brand logo. Every icon has a text label or an `aria-label`.
- **Glass surfaces (v1.1):** use a frosted-glass effect (translucent surface + `backdrop-filter: blur()` + a subtle border and highlight) on the floating chrome:
  - top bar;
  - sticky composer;
  - desktop sidebar;
  - mobile drawer, dialogs and toasts;
  - optionally the office card header.

  Content cards stay solid for readability. Rules:
  - text on glass must still pass WCAG AA (check it against the worst-case background behind it);
  - provide a solid fallback for `@supports not (backdrop-filter: blur(1px))` and for `prefers-reduced-transparency: reduce`;
  - keep the blur radius modest and the glass layers to the few listed above, so low-end Android stays smooth;
  - add a soft background (gradient or shapes) behind the glass so the effect is visible;
  - all glass values (alpha, blur, border, shadow) are tokens.
- **UX polish (v1.1):**
  - clearer visual hierarchy: answer title and summary first, stronger section headers, more breathing room;
  - refined spacing and type rhythm;
  - polished empty, loading and error states;
  - smooth micro-interactions (reduced-motion safe);
  - obvious primary actions;
  - a more modern, friendly feel, while staying calm and not looking like a government site.

## 4. Screens

Routes match `03-frontend-plan.md`. Each screen gets mobile (375) and desktop (1280) layouts, plus every state listed.

| # | Screen / route | Must show | States |
|---|---|---|---|
| 0 | **Landing `/welcome`** (public, first visit) | What GovAssist does in one sentence, 3 steps (ask → get steps & documents → go to the right office), one sample answer card preview (NAMUNA), Sign up (primary), Log in, language switch, "Not an official government service", About/Privacy links | default (mobile + desktop) |
| 1 | Sign up `/signup` | Email, password (with strength hint), Turnstile, "Continue with Google", link to log in, privacy note | default, field errors, submitting, server error |
| 2 | Log in `/login` | Email, password, Google, forgot password, link to sign up | default, wrong credentials, social error, submitting |
| 3 | Check your email | "We sent a link to <email>", resend, change email | sent, resent, rate-limited |
| 4 | Verify email `/verify-email/:key` | Result | verifying, success → continue, invalid/expired link |
| 5 | Forgot / reset password | Email form; new password form | default, sent, invalid key, success |
| 6 | Onboarding `/onboarding` | Step 1: UI language. Step 2: region → district (searchable list, dependent). Why we ask | default, loading districts, validation, saving |
| 7 | **Chat, empty** `/` | Greeting, input, 4–6 suggested question chips, short "what I can help with" | default, suggestions loading |
| 8 | **Chat, answering** | User bubble, **progress line** ("Searching documents…", "Found 4 sources", "Writing answer…"), office card appearing early, answer cards filling in live, **Stop** button | each stage, live streaming |
| 9 | **Answer: service** | Title, summary, numbered steps, documents checklist, fee + processing time row, **office card**, sources list, citation badges `[1]` on items, disclaimer, feedback 👍/👎 (+ optional comment), follow-up chips | complete, partially cited, office `match=region` (note: "nearest in your region"), `match=none` ("office address not available yet"), no office |
| 10 | **Answer: legal** | Short answer, "What the law says" (quote block + plain explanation + article citation), "What you can do" steps, sources, disclaimer | complete |
| 11 | Answer: not found / off topic | Polite message, suggestions to rephrase or browse common topics | both |
| 12 | Chat errors | Inline error under the message with **Retry**; rate limit with "try again in N min"; quota reached; offline banner | each |
| 13 | History `/history` (mobile) / sidebar (desktop) | Conversation list: title, preview, date; delete with confirm; "New chat" | empty, list, loading, deleting |
| 14 | Settings `/settings` | UI language, region/district, account (email, change password, log out, **delete account** with confirm), quota usage | default, saving, confirm dialogs |
| 15 | About `/about` | What GovAssist is, how answers are made (sources, no legal advice), privacy (what is stored, PII scrubbing), "not an official government service", source list | — |
| 16 | 404 / generic error | Friendly message, home link | — |

Layout:
- **Desktop:** left sidebar (history + new chat), centered chat column (max ~760 px), sticky input at the bottom.
- **Mobile:** top bar (menu, title, new chat), full-width chat, sticky input; history opens in a drawer.

### 4a. End-to-end journeys (required)

The design must be **clickable from first visit to the last action**, not a gallery of separate screens. Every primary button or link goes to the next screen of its journey. Each journey has its own content: no reusing the passport answer everywhere. All facts stay NAMUNA/SAMPLE.

| # | Journey | Path |
|---|---|---|
| J1 | **New user, service question** (uz-Latn) | Landing → Sign up → Check email → Verify (success) → Onboarding: language → region/district → Chat empty → tap the suggestion "Pasportimni qanday yangilayman?" → streaming: searching → found → office card early → summary → steps → documents → fee/time → final → 👍 feedback → tap a follow-up chip → **second turn in the same thread** (a short service answer) |
| J2 | **Returning user, legal question** (uz-Cyrl question and answer) | Landing → Log in → Chat (desktop: sidebar with history) → New chat → type a factual labour-law question → streaming → **legal answer** (law points with quote + explanation, steps "what you can do", sources) → open a source |
| J3 | **Russian question, region fallback** | Chat → Russian question → service answer in Russian → office card `match=region` with unknown hours → open Google Maps |
| J4 | **Not found / off topic, then recovery** | Off-topic question → off_topic answer → tap a topic chip → a not_found answer → rephrase → service answer |
| J5 | **Errors** | Streaming → **Stop** → "Answer stopped" → Retry → final answer. Plus: rate-limited (`retry_after`), quota reached (`scope` user vs global), offline banner → back online |
| J6 | **Account** | History → open an old conversation → delete with confirm → Settings → switch the UI language to Russian (UI updates) → change password → Log out → Landing. Plus Login → Forgot password → email sent → Reset → success → Log in |

Streaming in J1–J5 **plays by itself** (timed stages, with a reduced-motion variant that jumps between stages). The final state of every journey is a real screen, not a note.

## 5. Components

Define each with its anatomy, variants, states (default, hover, focus, active, disabled, loading, error) and tokens used.

- **Basics:** Button (primary, secondary, ghost, danger; sizes), IconButton, TextField, PasswordField, Select/Combobox (searchable, for districts), Checkbox, Chip (suggestion, follow-up), Badge (citation `[n]`, open/closed), Alert/Banner, Toast, Dialog (confirm), Drawer, Skeleton, Spinner, Tabs (optional), Divider, Link (internal, external with icon).
- **Chat:** MessageBubble (user), AssistantMessage container, ProgressLine (stage + animated dots, reduced-motion safe), InputBar (auto-grow textarea, send, stop, character counter at 900+/1000), FeedbackBar.
- **Answer cards:** AnswerHeader (title + summary), StepsList (numbered, citation badges), DocumentsChecklist (tick-able, visual only), FactsRow (fee + processing time), LawPointCard (quote + explanation + citation), SourcesList (publisher, title, section, date, external link), Disclaimer, FollowUpChips.
- **OfficeCard:**
  - name, type label, address;
  - **"Open now / Closed / Opens at 09:00"** badge (computed client-side in Asia/Tashkent);
  - weekly hours table (collapsible) with the lunch break;
  - phone (tap to call);
  - **"Open in Google Maps"** button;
  - "data as of <date>" and a source link;
  - variants: district match, region match, none.
- **Streaming behaviour:**
  - Show how each card looks while its text is still arriving: a skeleton until the first characters, then the text growing.
  - Cards appear in schema order: summary → steps → documents → fee/time → law points.
  - When `final` arrives, nothing may jump, so reserve space sensibly.

## 6. Content and copy

- Write UI copy in **Uzbek Latin and English** in `docs/design/copy.md`, as a table: key, uz-Latn, en, max length. The frontend lane adds ru and uz-Cyrl.
- Tone: friendly, short, second person, no jargon or bureaucratic phrasing.
- Required strings:
  - the disclaimer ("This is general information, not legal advice. Check the official source.");
  - "Not an official government service";
  - every error message;
  - progress-line stages;
  - office states.
- Use the illustrative example in `docs/contract.md` §6 for mock content. **Never invent real-looking fees, addresses or phone numbers.** Keep the `NAMUNA`/`SAMPLE` markers.

## 7. Deliverables (all in `docs/design/`)

| File | Content |
|---|---|
| `README.md` | Overview, file index, **Status: Draft / In review / Approved**, open questions |
| `design-system.md` | Principles, typography, color (with contrast table), spacing, radius, elevation, motion, icons, accessibility rules |
| `tokens.json` | W3C Design Tokens format: color (light, optional dark), typography, spacing, radius, shadow, motion, breakpoints |
| `tokens.css` | The same tokens as CSS custom properties (`--color-…`, `--space-…`). **The frontend imports this file directly**, so it is the single source and must not be duplicated |
| `components.md` | Each component: anatomy, variants, states, tokens, accessibility notes (role, keyboard, aria) |
| `screens.md` | Each screen in §4: purpose, layout per breakpoint, components used, states, copy keys, data fields from the contract |
| `copy.md` | UI strings, uz-Latn + en |
| `prototype/*.html` | Static, **no-build** HTML + CSS prototype using `tokens.css`. One file per screen and state group, with an `index.html` linking them. Must work by opening the files directly |
| `screenshots/` | PNGs of every prototype screen at 375×812 and 1440×900 (for review and thesis figures) |
| `prototype/journeys.html` | Start page listing J1–J6 (§4a), each with a "Start" link into a fully linked click-through |
| `prototype/flow.js` | One small shared script (vanilla JS, no framework) for journey navigation, form submits, and timed streaming playback |
| `screenshots/journeys/` | Every step of J1–J6 in order, at 375×812 (`J1-01-landing.png` …), for review and the thesis |
| **Design canvas** (Claude Design artifact) | Mirrors the prototype. **Every screen** of §4 as artboards (phone 390 wide; desktop 1440 for chat, history and settings), arranged one row per journey with a title note each, and prototype links between artboards so a viewer can click through J1–J6. Not just a sample of three screens |

Prototype rules:
- semantic HTML, so it doubles as the markup reference for React;
- no JavaScript frameworks; small inline JS for state toggles, plus the shared `flow.js` for journeys;
- no external CDNs.

## 8. Review checklist (main session approves at G2)

- [ ] Every screen and state in §4 is present in `screens.md`, the prototype and the screenshots.
- [ ] All answer types (service, legal, not_found, off_topic), every office variant and the streaming stages are designed.
- [ ] Data shown matches `docs/contract.md` field by field, and nothing needs data the API doesn't provide.
- [ ] Contrast table passes AA, targets ≥ 44 px, focus states visible, reduced-motion variant defined.
- [ ] 375 px layouts don't overflow with long Russian/Cyrillic strings. A test string set is included.
- [ ] The font renders oʻ gʻ (U+02BB) and ў қ ғ ҳ correctly. Screenshot proof included.
- [ ] `tokens.css` and `tokens.json` agree and cover every value used in the prototype (no raw hex in the prototype CSS).
- [ ] No official-government imitation. The disclaimer and the "not official" note are present.
- [ ] No invented real facts. Sample markers kept.
- [ ] The prototype opens offline with no build step.
- [ ] **J1–J6 are clickable end to end**, in both the prototype and the design canvas. No dead ends: every primary action leads somewhere.
- [ ] The landing page exists. J1 includes a second turn in the same thread. J2 shows a full legal answer. J3 shows a Russian answer.
- [ ] Streaming plays by itself in the journeys, with a reduced-motion variant.
- [ ] `screenshots/journeys/` has every step of every journey.
- [ ] (v1.1) Every icon is a real Lucide icon from one pinned `lucide-static` version, and the inventory is in `components.md`.
- [ ] (v1.1) Glass is on the listed chrome only, AA passes on glass, and the solid fallbacks for no-`backdrop-filter` and reduced transparency are designed and screenshotted.
- [ ] (v1.1) A UX polish pass is done, with a before/after list in the README.

---

## 9. Prompt for the design session

Copy everything inside the block into a new Claude Code session opened at the repo root.

```text
You are Sevara (Claude), the product designer for GovAssist, an MSc thesis project: a RAG-based web assistant
that tells citizens of Uzbekistan how to get a public service and exactly which office to visit.

Work only in the git worktree `.claude/worktree/design` on branch `design/system-v1` (create it as described in
AGENTS.md → Worktrees), and only inside `docs/design/`.

Read first, fully:
1. /AGENTS.md (repo rules)
2. docs/plans/00-main-plan.md (product, decisions)
3. docs/contract.md (every field a screen can show; §6 example data)
4. docs/plans/01-design-plan.md (your plan; follow §1–§8 exactly)

Your job: produce the complete design system, all screens defined in 01-design-plan.md §4–§5, and the clickable
end-to-end journeys J1–J6 in §4a (prototype and design canvas), as the deliverables listed in §7:
docs/design/{README.md, design-system.md, tokens.json, tokens.css, components.md, screens.md, copy.md,
prototype/*.html, prototype/journeys.html, prototype/flow.js, screenshots/*.png, screenshots/journeys/*.png},
plus the design canvas (every screen as artboards, one row per journey, prototype links between artboards).

Hard rules:
- You own this lane and do all of it yourself. Do NOT use Antigravity (`agy`) for any design work.
- Check each screen when it is finished (open it at 375 and 1440 px, run the contrast check) before starting the next.
- Phone-first (375 px), WCAG 2.2 AA, touch targets ≥ 44 px, body ≥ 16 px, reduced-motion support.
- Must not look like an official government site: no emblem, no flag branding, no my.gov.uz look-alike.
  Include "Not an official government service" and the answer disclaimer.
- tokens.css is the single source of design values; the prototype CSS uses only its variables (no raw hex).
- The prototype is static HTML + CSS, no build step, no CDN, semantic markup. JS: small inline toggles plus one
  shared vanilla `prototype/flow.js` for journey navigation and timed streaming playback.
- The font must render Uzbek Latin oʻ gʻ (U+02BB) and Uzbek Cyrillic ў қ ғ ҳ; prove it in a screenshot.
- Base content on docs/contract.md §6. Content the journeys need beyond it (legal, Russian, off-topic answers) is
  written as NAMUNA/SAMPLE placeholders. Never invent real-looking fees, addresses, phone numbers or law articles.
- Do not change docs/contract.md. If a screen needs data the contract lacks, list it under "Open questions"
  in docs/design/README.md instead of designing around it.
- Make screenshots with a headless browser (Playwright) at 375×812 and 1440×900.

When finished:
1. Self-check against 01-design-plan.md §8 and tick each box in docs/design/README.md (Status: In review).
2. Commit with Conventional Commits (e.g. "feat(design): add design system v1"), push the branch, open a PR to main
   titled "Design system v1", with the §8 checklist in the description.
3. Remove your worktree from the repo root: `git worktree remove .claude/worktree/design && git worktree prune`
   (never --force).
4. Report back: PR link, list of screens, open questions, anything you could not do.
The main session will review the PR and approve it (G2) or request changes.
```
