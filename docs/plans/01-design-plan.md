# Design Plan: Design System and Screens

**Lane:** Design. **Agent:** Sevara (Claude). **Branch:** `design/system-v1` (own worktree).
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
- **Icons:** one outline set. Lucide is recommended because the frontend uses `lucide-react`. Every icon has a text label or an `aria-label`.

## 4. Screens

Routes match `03-frontend-plan.md`. Each screen gets mobile (375) and desktop (1280) layouts, plus every state listed.

| # | Screen / route | Must show | States |
|---|---|---|---|
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

Prototype rules:
- semantic HTML, so it doubles as the markup reference for React;
- no JavaScript frameworks; tiny inline JS only to toggle states;
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

---

## 9. Prompt for the design session

Copy everything inside the block into a new Claude Code session opened at the repo root.

```text
You are Sevara (Claude), the product designer for GovAssist, an MSc thesis project: a RAG-based web assistant
that tells citizens of Uzbekistan how to get a public service and exactly which office to visit.

Work only in a git worktree on branch `design/system-v1`, and only inside `docs/design/`.

Read first, fully:
1. /AGENTS.md (repo rules)
2. docs/plans/00-main-plan.md (product, decisions)
3. docs/contract.md (every field a screen can show; §6 example data)
4. docs/plans/01-design-plan.md (your plan; follow §1–§8 exactly)

Your job: produce the complete design system and all screens defined in 01-design-plan.md §4–§5,
as the deliverables listed in §7:
docs/design/{README.md, design-system.md, tokens.json, tokens.css, components.md, screens.md, copy.md,
prototype/*.html, screenshots/*.png}.

Hard rules:
- Phone-first (375 px), WCAG 2.2 AA, touch targets ≥ 44 px, body ≥ 16 px, reduced-motion support.
- Must not look like an official government site: no emblem, no flag branding, no my.gov.uz look-alike.
  Include "Not an official government service" and the answer disclaimer.
- tokens.css is the single source of design values; the prototype CSS uses only its variables (no raw hex).
- The prototype is static HTML + CSS (tiny inline JS for state toggles only), no build step, no CDN, semantic markup.
- The font must render Uzbek Latin oʻ gʻ (U+02BB) and Uzbek Cyrillic ў қ ғ ҳ; prove it in a screenshot.
- Use only the illustrative data from docs/contract.md §6. Never invent real-looking fees, addresses or phone numbers.
- Do not change docs/contract.md. If a screen needs data the contract lacks, list it under "Open questions"
  in docs/design/README.md instead of designing around it.
- Make screenshots with a headless browser (Playwright) at 375×812 and 1440×900.

When finished:
1. Self-check against 01-design-plan.md §8 and tick each box in docs/design/README.md (Status: In review).
2. Commit with Conventional Commits (e.g. "feat(design): add design system v1"), push the branch, open a PR to main
   titled "Design system v1", with the §8 checklist in the description.
3. Report back: PR link, list of screens, open questions, anything you could not do.
The main session will review the PR and approve it (G2) or request changes.
```
