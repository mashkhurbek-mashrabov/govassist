# Components

Each component lists anatomy, variants, states, tokens and accessibility. The class names are the ones in [`prototype/proto.css`](prototype/proto.css); see them all on [`prototype/components.html`](prototype/components.html). The React lane builds the same anatomy in `components/ui` and `features/answer`, styled with Tailwind utilities mapped to [`tokens.css`](tokens.css).

**Shared states** (apply to every interactive component unless noted):

| State | Treatment |
|---|---|
| default | as specified |
| hover | one step darker (`*-hover`) or `--color-surface-sunken` background |
| focus | `:focus-visible` 3 px `--color-focus-ring` outline, 2 px offset |
| active | `*-active` (primary) |
| disabled | `--color-surface-sunken` background, `--color-text-disabled`, `--color-border`, `cursor: not-allowed`, native `disabled` |
| loading | spinner replaces the icon, label changes to the "…-ing" copy key, `aria-busy="true"`, `disabled` |
| error | `--color-danger` 2 px border + `.field__error` (icon + text), `aria-invalid="true"` |

Every motion uses `--motion-*` tokens and stops under `prefers-reduced-motion`.

---

## Basics

### Button `.btn`
- **Anatomy:** optional leading icon (20 px) · label · optional trailing icon (external link).
- **Variants:** `--primary` (one per screen), `--secondary` (surface + strong border), `--ghost` (link-coloured, no border), `--danger`, `--danger-ghost` (destructive entry point, e.g. "Hisobni oʻchirish"), `--google` (surface + Google "G" mark).
- **Sizes:** md 48 px (`--size-control`, default), `--sm` 44 px (`--size-touch-min`). `--block` = full width (auth forms, mobile dialogs).
- **States:** all shared states.
- **Tokens:** `--color-primary*`, `--color-on-primary`, `--color-danger*`, `--color-border-strong`, `--radius-md`, `--space-2/4/5`, `--font-weight-semibold`.
- **A11y:** native `<button>`; a navigating button is an `<a>`. Loading keeps the width (no layout jump) and announces the new label.

#### "Continue with Google" variant `.btn--google`
Used on Sign up and Log in (screens 1 and 2, journeys J1, J2, J6). It posts the allauth provider-redirect form (contract §2).
- **Anatomy:** Google "G" mark · label "Google orqali davom etish" / "Continue with Google" (`auth.google`). The mark sits left of the label, vertically centred.
- **Size and spacing:** the same as every button: 48 px high (`--size-control`), full width in auth forms (`--block`), `--space-5` side padding, `--radius-md`. The mark is 20 × 20 px (`--size-icon`) with `--space-2` (8 px) between mark and label. The mark is never scaled below 20 px or above 24 px.
- **Colours:** surface background (`--color-surface`), `--size-border` border in `--color-border-strong`, label in `--color-text`; hover `--color-surface-sunken`. The mark keeps **Google's four brand colours, unaltered** (Google sign-in branding rules): `--color-google-blue`, `-green`, `-yellow`, `-red`. It is never tinted, outlined, put on a coloured fill or recoloured for the dark theme.
- **Brand-colour exception:** these four are the only tokens that are not part of the GovAssist palette. Their hex values live once in `tokens.css` (`--palette-google-*`) and the prototype uses them only through the `.g-blue` / `.g-green` / `.g-yellow` / `.g-red` classes on the SVG paths, so `tokens.mjs --check` passes with no whitelist. No other component may use them.
- **Markup:** inline SVG (24 px viewBox, `stroke: none`, four `<path>`s), `aria-hidden="true"`; the visible label is the accessible name. See `prototype/signup.html`.
- **States:** default, hover, focus (standard ring), loading (spinner replaces the mark, label kept), disabled (shared disabled style; the mark stays in colour).

### IconButton `.icon-btn`
- 44 × 44 px, icon 20 px. Variants: default (transparent), `--primary` (send), toggle (`aria-pressed="true"` → subtle primary fill: feedback 👍/👎).
- **A11y:** always an `aria-label`; toggles use `aria-pressed`.

### TextField `.field` + `.input`
- **Anatomy:** label (16 px semibold) · input (48 px) · hint (14 px muted) · error (14 px danger with icon).
- **States:** default, focus (border and ring in primary), filled, disabled, error.
- **A11y:** `<label for>`, hint and error in `aria-describedby`, `aria-invalid`, correct `type` and `autocomplete`.

### PasswordField
- TextField + trailing IconButton (eye) that toggles visibility (`aria-pressed`, label switches between `auth.password_show` and `auth.password_hide`).
- **Strength hint** (signup, reset): 3-segment meter `.strength[data-level=1|2|3]` (danger / warning / success) + text "Parol kuchi: kuchsiz / oʻrtacha / kuchli" in a polite live region. The meter is `aria-hidden`; the text carries the meaning. Rule shown in the hint: at least 10 characters.

### Select / Combobox `.combobox`
- **Native `<select>`** for short fixed lists (UI language).
- **Searchable combobox** for region and district: leading search icon · input (`role="combobox"`, `aria-expanded`, `aria-controls`, `aria-autocomplete="list"`) · chevron · popup `.listbox` (`role="listbox"`, options `role="option"`, `aria-selected`, active option highlighted, check mark on the selected one).
- **States:** closed, open, filtering, loading (spinner + "Tumanlar yuklanmoqda…" + skeleton rows), empty ("Hech narsa topilmadi"), disabled with a reason ("Avval viloyatni tanlang"), error.
- **Keyboard:** ↓/↑ move, Enter selects, Esc closes, typing filters (match both scripts: the frontend's transliteration lets "Чилонзор" find "Chilonzor").
- **Dependent:** changing the region clears the district and reloads `/geo/regions/{id}/districts`.

### Checkbox `.check`, RadioCard `.radio-card`
- Native inputs with `accent-color: var(--color-primary)`, 24 px box, whole row clickable at ≥ 44 px. RadioCard (onboarding language) shows a 2 px primary border and subtle fill when checked (`:has(input:checked)`).

### Chip `.chip`
- **Variants:** suggestion (empty chat), follow-up (after an answer), topic (not-found). Same look: 44 px min height, `--radius-lg`, subtle primary border, primary text; wraps onto several lines for long Russian text.
- **A11y:** `<button>` inside a `<ul class="chips">`; clicking sends the text as a new question.

### Badge `.badge`
- **Office state:** `--open` "Hozir ochiq · 18:00 gacha", `--break` "Tushlik tanaffusi · 14:00 da ochiladi", `--closed` "Yopiq · 09:00 da ochiladi" / "Yopiq · Dushanba 09:00 da ochiladi", `--neutral` "Ish vaqti nomaʼlum". A coloured dot plus text, 13 px semibold.
- **Citation badge `.cite`:** number `n` = position of the source in `sources` (S1 → 1). 24 px visual, 44 px hit area, 12 px apart. It is a link to `#src-n`; the target source gets a subtle highlight (`:target`). `aria-label="{n}-manba"`. Items whose `source_ids` are empty show no badge.

### Alert / Banner / Toast
- **Alert `.alert`:** icon · body (optional title, text, optional actions). Variants: info (default), `--success`, `--warning`, `--danger`. `role="alert"` for errors that stop the user, `role="status"` otherwise.
- **Banner `.banner`:** full-width strip under the top bar (offline). Warning colours, `role="status"`.
- **Toast `.toast`:** bottom centre, `--shadow-2`, auto-hides after 4 s, `role="status"`; never the only way to see an error.

### Dialog `.dialog` (confirm)
- **Anatomy:** title · body · actions (Cancel secondary + destructive danger). Optional confirm checkbox (delete account) that enables the destructive button.
- **Layout:** bottom sheet on phones (actions stacked, destructive on top), centred 448 px (`--size-dialog`) from 768 px.
- **A11y:** `role="alertdialog"`, `aria-modal`, `aria-labelledby`, `aria-describedby`; focus moves to Cancel, is trapped, returns to the trigger; Esc and the scrim cancel.

### Drawer (mobile history)
- The sidebar slides in from the left over a scrim, `min(296 px, 86vw)` wide. Opened by the top-bar menu button (`aria-controls="sidebar"`, `aria-expanded`), closed by ×, the scrim or Esc. From 1280 px the same element is a permanent sidebar.

### Skeleton `.skeleton`, Spinner `.spinner`
- Skeleton bars (16 px, title 24 px; widths 100/80/60/40 %) with a shimmer that becomes flat grey under reduced motion. Skeletons are `aria-hidden`; a visually hidden "Yuklanmoqda…" status goes with them.
- Spinner: 20 px ring in `currentColor`; used inside buttons and the verify screen.

### Divider, Link
- `.divider` 1 px `--color-border`; `.divider-text` for "yoki".
- **Internal link:** `--color-link`, underlined. **External link:** same plus the external-link icon, `target="_blank" rel="noopener noreferrer"` and a visually hidden "(yangi oynada ochiladi)".

### Tabs
Optional in the plan and not needed by any screen, so not designed.

### Landing parts (screen 0)
- **Hero** `.landing__hero`: display heading, lead, actions (Sign up primary, Log in secondary; full width on phones, side by side from 768 px), small note. Two columns from 1280 px.
- **Sample answer preview** `.landing__preview`: a `figure` with caption "Javob namunasi · NAMUNA" and a raised card that reuses AnswerHeader, StepsList and the OfficeCard badge row. Citation badges are plain `span`s (`aria-hidden`), not links, because there are no sources on the page.
- **HowStep** `.how-step`: icon tile (40 px, primary-subtle) · h3 · muted text; three in a row from 768 px.

### ChangePasswordForm (Settings → Account)
Inline form card inside the Account card: title "Parolni oʻzgartirish", or "Parol oʻrnatish" + one-line explanation when `Me.has_password` is false · current password (PasswordField, only when `has_password`) · new password (PasswordField + strength + hint) · Save (primary, busy while saving) + Cancel (ghost). Errors: wrong current password on the field. Success replaces the form with a success Alert "Parol oʻzgartirildi.".

---

## Chat

### MessageBubble (user) `.msg-user`
Right-aligned, max 85 % width, `--color-user-bubble`, `--radius-lg` with a small bottom-right corner. Shows the stored (PII-scrubbed) text, so placeholders such as `[PASSPORT]` appear as plain text. A visually hidden "Siz:" prefix.

### AssistantMessage `.assistant`
A full-width column, 16 px gap, visually hidden "GovAssist javobi:" prefix. `aria-busy="true"` while streaming. It holds, in order: ProgressLine → AnswerHeader → cards (per `answer_type`, see screens.md) → Disclaimer → FeedbackBar → FollowUpChips.

### ProgressLine `.progress`
- **Anatomy:** three pulsing dots · optional "✓ 4 ta manba topildi" · stage text.
- **Stages** (from `status.stage`): `searching` → "Hujjatlar qidirilmoqda…"; `found` → "✓ {count} ta manba topildi"; `writing` → "✓ 4 ta manba topildi · Javob yozilmoqda…". The found count stays visible once known. After `final` the line is removed; after Stop it becomes "■ Javob toʻxtatildi. Savolni qayta yuborishingiz mumkin." The partial cards stay for this view only (the backend stores no partial answer). After a reload the stored message (`status: failed`, `error_code: "stopped"`) renders as a warning Alert "Javob toʻxtatildi" with **Retry**; other `error_code`s use their error copy (screen 12).
- **Reduced motion:** dots solid, text unchanged.
- **A11y:** `role="status"`, `aria-live="polite"`; announces only stage changes.

### InputBar `.composer` / `.inputbar`
- **Anatomy:** auto-grow textarea (1 line → max 160 px, then scrolls; `field-sizing: content`) · Send IconButton (primary) **or** Stop button (secondary, with label) while streaming · note "Rasmiy davlat xizmati emas. Javoblarda xato boʻlishi mumkin." · character counter.
- **Counter:** hidden below 900 characters; from 900 it shows `940 / 1000` in warning colours; over 1000 it shows danger colours, a danger border on the bar, the message "Savol juda uzun…" and a disabled Send.
- **States:** idle (Send disabled while empty), typing, streaming (Stop), disabled (offline, rate-limited, quota), over-limit.
- **Keyboard:** Enter sends, Shift+Enter adds a new line; focus stays in the textarea after sending.
- **Layout:** sticky at the bottom, aligned with the chat column (max 760 px).

### FeedbackBar `.feedback`
"Javob foydali boʻldimi?" + 👍 / 👎 toggle buttons (`aria-pressed`). Choosing 👎 opens an optional comment (≤ 1000 characters) with a Send button; 👍 saves at once. Saved state: "✓ Rahmat! Fikringiz saqlandi." The saved rating stays pressed, and changing it updates the same `Feedback` (upsert).

---

## Answer cards

| Component | Class | Content (contract field) | Notes |
|---|---|---|---|
| AnswerHeader | `.answer-head` | kind label (`answer_type`), `title` (h2), `summary` (body-lg) | Kind label with compass (service) or scale (legal) icon |
| StepsList | `.card` + `.steps` | `steps[].text` + badges from `source_ids` | Numbered circles 32 px; heading "Nima qilish kerak" (service) or "Nima qilishingiz mumkin" (legal) |
| DocumentsChecklist | `.doc-list` + `.check` | `documents[]` | Tick-able, visual only; hint "Belgilar saqlanmaydi" |
| FactsRow | `.facts` + `.fact` | `fee`, `processing_time` | Two tiles side by side when ≥ 240 px each, else stacked. `null` → "Manbalarda koʻrsatilmagan" |
| LawPointCard | `.law` | `law_points[].quote` (blockquote), `.explanation`, `source_ids` | Labels "Qonun matni" / "Oddiy tilda"; badge after the explanation; the section reference comes from the cited source's `section` |
| SourcesList | `.sources` + `.source` | `sources[]`: number, `title` (external link), `publisher` · kind · `section` · `published_at` · `fetched_at` | Listed in contract order (first citation); number matches badges; `:target` highlight |
| Disclaimer | `.disclaimer` | static `app.disclaimer` | Always under the answer, all types |
| FollowUpChips | `.followups` | `follow_up_questions[]` (≤ 3) | Hidden when empty |

---

## OfficeCard `.office`

**Anatomy, top to bottom:**
1. Card heading "Qayerga borish kerak" (map-pin icon).
2. *(region match only)* warning alert: "Tumaningizda bunday idora topilmadi, shuning uchun hududingizdagi boshqa idora koʻrsatildi."
3. Type label (`office_type.label`, building icon) and the open-state **badge** on one row (wraps on phones).
4. Office `name` (h3 size, semibold).
5. Address row: `address`, `district.name`, `region.name`.
6. **Working hours** `<details>`, collapsed by default: a table of day groups → `open – close`, the lunch break under it, missing days as "Dam olish kuni", today's row in bold.
7. Actions: **phone** (secondary, `tel:` link, the number never wraps) and **"Google Xaritada ochish"** (primary, `href=map_url`, new tab). Side by side from 768 px, stacked on phones.
8. Meta: "Maʼlumot {data_as_of} holatiga" · "Manba" (external link to `source_url`).

**Open-state badge** (computed in the browser for Asia/Tashkent from `working_hours`):

| Condition | Badge |
|---|---|
| inside open hours, not in break | `--open` "Hozir ochiq · {close} gacha" |
| inside the break | `--break` "Tushlik tanaffusi · {break.end} da ochiladi" |
| before opening today | `--closed` "Yopiq · {open} da ochiladi" |
| after closing, or a day off | `--closed` "Yopiq · {next day} {open} da ochiladi" |
| `working_hours` empty | `--neutral` "Ish vaqti nomaʼlum", and no hours table |

**Variants:**

| `match` | Shows |
|---|---|
| `district` | the full card |
| `region` | the full card + warning alert (2) |
| `none` | heading, type label, info alert "Bu idora manzili hozircha bazamizda yoʻq. Kerakli idora: {office_type.label}." No address, buttons or meta |
| no `office` event and `final.office = null` | no card at all |
| `phone = null` | "Telefon raqami nomaʼlum" text row instead of the call button |

**Streaming:** the card can arrive (`office` event) before any answer text; it renders complete straight away, below the skeleton for the header, and then keeps its place while the other cards fill in above it.

**A11y:** `section` with `aria-labelledby`; the hours `<table>` has a caption and row headers; the map link says it opens a new tab; the badge text is real text, not colour only.

---

## Journey playback (prototype only)

`prototype/flow.js` is not a product component. It shows how streaming should *feel*: each stage holds for about 1–2.5 s, the growing text types out, and the next block's skeleton holds its place. In the product the timing comes from the SSE stream. The journey bar's **Pause** stops the timer (WCAG 2.2.2); with reduced motion the text appears at once and the page jumps from stage to stage.

## Streaming behaviour

- **Order is fixed by the schema:** summary → steps → documents → fee/time → law points. The office card (from the `office` event) sits after fee/time and is placed as soon as it arrives.
- **Before the first characters of a block:** a skeleton shaped like that block (title bar + 2 lines for the header; 2 step rows; a card for the next block; two tiles for fee/time). At most one skeleton block ahead of the text, so the page never fills with grey.
- **While text arrives:** the growing text is shown with a block caret (`.typing`, still under reduced motion). Citation badges appear when their `source_ids` are parsed.
- **No jump on `final`:** cards keep their positions. `final` replaces the text with the validated version (usually identical) and adds the sources card, disclaimer, feedback and follow-ups *below* the content, so nothing above moves. Badges whose IDs `final` removed disappear in place.
- **Stop:** the stream is aborted. The partial cards stay visible and the ProgressLine shows the stopped message (see the README open questions about how a stopped message is stored).
