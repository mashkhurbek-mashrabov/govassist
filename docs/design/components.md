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

### Logo and wordmark
The author's design (`brand/logo-source.jpeg`), redrawn as clean SVG from primitives rather than auto-traced: one ring with a speech tail, a map-pin point under it, and a check inside. It means "your question, answered, and the place to go". Files are in [`brand/`](brand/), and [`prototype/brand.html`](prototype/brand.html) shows them all.

| File | Use |
|---|---|
| `logo-mark.svg` | The mark with its gradient (`#4647D5` → `#9B44F3`, horizontal; tokens `--palette-logo-indigo` / `--palette-logo-violet`). From 48 px up. |
| `favicon.svg` | The **small cut**: thicker ring and check, wider pin gap. For 16–32 px and for the wordmark. It switches to lighter stops in `prefers-color-scheme: dark`. |
| `logo-mark-mono.svg` | One colour (`currentColor`; ink `#1C1917` when used as an image). For one-colour print and stamps. |
| `logo-lockup.svg` | Mark + "GovAssist" in Inter SemiBold, outlined (no font needed). |
| `favicon.ico` | 16, 32, 48 (PNG inside ICO) for old browsers. |
| `apple-touch-icon.png` | 180, white full bleed (iOS rounds the corners). |
| `icon-192.png`, `icon-512.png` | PWA "any" icons: the mark on a white rounded square. |
| `icon-512-maskable.png` | PWA maskable: white full bleed, the mark inside the central 80 % safe circle. |
| `proof-small-sizes.png` | Legibility proof: the favicon at 16 / 24 / 32 px on light and dark, real size and 8× zoom. |

- **Why a white tile for the app icons:**
  - the source is drawn on white;
  - white keeps both gradient ends at 3:1 or better on any wallpaper or tab colour (the indigo end is only 2.6:1 on dark grey);
  - a gradient tile would need a second, white mark and lose the gradient identity.
- **Wordmark** `.wordmark`: the small-cut mark in a `--size-logo` (32 px) box, a `--space-1` gap, then "GovAssist" in the h3 size, semibold.
  - In the prototype the mark is inline SVG, and its stops come from `--color-logo-start` / `--color-logo-end`. Dark theme maps them to `--palette-indigo-300` / `--palette-logo-violet-light`.
  - React: one `<LogoMark />` component, with unique gradient and mask ids per instance (`useId`).
- **Sizes:** minimum 16 px (`--size-logo-min`), and only the small cut there. Use the small cut up to 32 px and the regular mark from 48 px.
- **Clear space:** at least twice the ring's stroke width around the mark (about 1/8 of its height). In the lockup, keep the gap as drawn.
- **Contrast** (graphic, 3:1):
  - light: 6.73 / 4.65 on white, 6.44 / 4.45 on neutral-50;
  - dark: 9.17 / 9.50 on neutral-950 with the light stops. The light-theme indigo would be 2.94 there, which is why dark uses other stops.
- **Don't:**
  - recolour it outside the two gradients and the mono version;
  - rotate, stretch or outline it;
  - put the gradient mark on a busy photo or on the brand gradient;
  - add the state emblem, flag colours or my.gov.uz styling;
  - use it as a badge of official status. The "Rasmiy davlat xizmati emas" note stays wherever the logo is prominent.
- **Web app head:** `<link rel="icon" href="/favicon.ico" sizes="48x48">`, `<link rel="icon" href="/favicon.svg" type="image/svg+xml">`, `<link rel="apple-touch-icon" href="/apple-touch-icon.png">`. The manifest lists `icon-192.png`, `icon-512.png` (purpose `any`) and `icon-512-maskable.png` (purpose `maskable`).

### App chrome on glass (v1.1)
Top bar, InputBar (composer), desktop sidebar, mobile drawer, Dialog and Toast use the **glass** treatment (`design-system.md` §8a): `--color-glass` (dialogs/toasts: `--color-glass-strong`), `backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate))`, a `--color-glass-border` hairline on the edge that meets content, and a 1 px `--color-glass-highlight` inner line. Nothing inside these surfaces changes: same text colours, same targets. With no `backdrop-filter` support or with `prefers-reduced-transparency: reduce`, the tokens switch to solid white and the blur to 0. Content cards are never glass.

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
- **Markup:** inline SVG (24 px viewBox, `stroke: none`, four `<path>`s, class `icon icon--brand`), `aria-hidden="true"`; the visible label is the accessible name. See `prototype/signup.html`. It is the only non-Lucide mark; `tokens.mjs --check` skips `icon--brand` and checks every other icon against `icons/`.
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
- The UI language uses LanguageMenu (below), not a native `<select>` (v1.2).
- **Searchable combobox** for region and district: leading search icon · input (`role="combobox"`, `aria-expanded`, `aria-controls`, `aria-autocomplete="list"`) · chevron · popup `.listbox` (`role="listbox"`, options `role="option"`, `aria-selected`, active option highlighted, check mark on the selected one).
- **States:** closed, open, filtering, loading (spinner + "Tumanlar yuklanmoqda…" + skeleton rows), empty ("Hech narsa topilmadi"), disabled with a reason ("Avval viloyatni tanlang"), error.
- **Keyboard:** ↓/↑ move, Enter selects, Esc closes, typing filters (match both scripts: the frontend's transliteration lets "Чилонзор" find "Chilonzor").
- **Dependent:** changing the region clears the district and reloads `/geo/regions/{id}/districts`.

### LanguageMenu `.lang-menu` (v1.2)
Replaces every native language `<select>`: landing header and footer, auth header, app sidebar. A menu button that opens a short list.

- **Anatomy.** Button `.lang-menu__btn`: `globe` icon · short code `.lang-menu__code` (UZ / ЎЗ / RU / EN, fixed `--size-lang-code` width so switching never shifts the layout) · `chevron-down`. Block variant `.lang-menu--block` (sidebar) adds the native name before the code and fills the width. Panel `.lang-menu__panel`: 4 items, each the native name (Oʻzbekcha, Ўзбекча, Русский, English; Uzbek items show "Lotin yozuvi" / "Кирилл ёзуви" under the name), a `.lang-tag` code chip and a `check` on the current one.
- **States.** *Closed:* ghost button, 44 px tall. *Hover:* `--color-surface-hover` fill. *Focus:* the standard focus ring. *Open:* `aria-expanded="true"`, chevron turns 180°, panel opens below the button (`--size-popover` wide, solid raised surface + `--shadow-2`; solid, not glass, because the header is already glass and a nested blur shows text through). `.lang-menu--up` opens above (footer, sidebar). *Selected item:* `aria-checked="true"`, primary-subtle fill, primary text, check visible. *Item hover/focus:* surface-hover fill + focus ring.
- **Phone (< 768 px): bottom sheet.** The panel becomes a sheet fixed to the bottom, with a grabber, the title "Til" and items `--size-control` (48 px) tall, over a scrim. The script moves the sheet and scrim to `<body>` while open (a parent with `backdrop-filter` would otherwise trap the fixed sheet) and puts them back on close. Tapping the scrim closes it.
- **Keyboard and ARIA.** Button: `aria-haspopup="menu"`, `aria-expanded`, `aria-controls`; a visually hidden "Tilni tanlash:" before the code (`lang.menu_label`). Panel: `role="menu"`, items `role="menuitemradio"` + `aria-checked`, roving `tabindex`. Enter / Space / ↓ on the button opens and focuses the current item; ↑ / ↓ / Home / End move; Enter / Space choose; Esc or Tab closes; focus goes back to the button. Outside click closes.
- **Switching.** Choosing a language changes the UI in place: the content region (`[data-lang-region]`) fades to 35 % for 200 ms, the text swaps, `<html lang>` updates, and a polite live region announces `lang.switched` in the new language ("Язык изменён"). No reload, no scroll jump. Reduced motion: instant swap, no fade. Signed in, the choice is also saved with `PATCH /me {ui_language}`; signed out, it changes only the page, and onboarding step 1 starts on that language.
- **Code.** `flow.js` (first IIFE) has the whole behaviour; `window.GovAssistLang.set(lang)` and `.open(menu)` are used by the gallery state buttons.

### LanguageCards `.lang-cards` (v1.2)
Large radio cards for choosing a language where it is the main task: onboarding step 1 and Settings → App language. A `fieldset` (hidden legend "Til") with 4 `label.lang-card`s, 2 × 2 from 768 px. Each card: native name (in its own `lang`), script hint for Uzbek, code tag, a check circle on the right. The native radio input is visually hidden but keeps focus and arrow-key behaviour. *Checked:* 2 px primary border, `--gradient-subtle` fill, check circle filled with `--gradient-brand`. *Focus:* focus ring around the card. Card height ≥ `--size-lang-card` (72 px).

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

### Landing parts (screen 0, v1.3)
The welcome page has to say **why GovAssist and not any chatbot**. Its structure takes ideas from my.gov.uz (a prominent search, service-category tiles with simple icons, popular questions). It uses none of that portal's branding, emblem, colours or icon assets: GovAssist keeps its own indigo identity, Lucide icons and the "not official" note, so nobody mistakes it for the official portal.

- **Header** `.lp__header`: sticky glass bar.
  - ≥ 1280 px: wordmark · anchor nav `.lp-nav` (Qanday ishlaydi · Nega GovAssist · Xizmatlar · Savollar) · LanguageMenu · "Kirish" (ghost) + "Roʻyxatdan oʻtish" (primary).
  - 768–1279 px: wordmark · LanguageMenu · the two auth buttons · hamburger.
  - < 768 px: wordmark · LanguageMenu · hamburger. The buttons move into the menu.
  - **Hamburger** `.lp-nav-toggle`: an icon button with `aria-expanded` + `aria-controls`. It opens `.lp-nav-panel` under the bar: the four section links (48 px rows) and Kirish / Roʻyxatdan oʻtish side by side. Esc closes and returns focus. Choosing a link closes it.
- **Hero** `.lp-hero` on `--gradient-mesh`: eyebrow chip · display-xl gradient headline · lead · **AskBox** · popular-question chips · note (`landing.cta_note`). ≥ 1280 px: text left, preview right.
- **AskBox** `.lp-ask`, the hero's main action.
  - A visible label (`landing.ask_label`), then a textarea ("Savolingizni yozing…") and a "Soʻrash" primary button with `arrow-right`, inside one raised field. The whole box gets the focus ring.
  - Phone: the button goes full width under the textarea.
  - Submitting an empty box does nothing (native `required`).
  - **Carrying the question:** the question is kept in `sessionStorage` (key `govassist.pendingQuestion`) and the user goes to Sign up. It is **never put in the URL** (it can contain personal data).
  - After onboarding, the frontend sends it as the first chat message and then clears it. The backend scrubs PII as for any question.
- **Popular chips** `.lp-popular`: three `.chip` links (`service.*_q`). Each carries its question the same way.
- **Streaming preview** `.lp-preview`: as in v1.2 (CSS keyframes over `--motion-duration-preview`, static under reduced motion). New in v1.3: it is **translated into the UI language** (question, kind label, progress text, title, summary, steps, office type, open badge; `PREVIEW` sample, NAMUNA). The office **name and address stay as stored** (contract v1.5), with `lang="uz-Latn"`.
- **ProblemList** `.lp-problem`: the heading "Notoʻgʻri idora — yoʻqotilgan kun", a lead, and 3 cards, each a warning-tinted icon tile + h3 + text:
  - wrong office (`map-pin-x`);
  - one missing document (`file-x`);
  - outdated advice (`clock-alert`).

  An answer strip `.lp-answer` follows: "GovAssist borishdan oldin hammasini bir joyda koʻrsatadi.". Qualitative only, no numbers.
- **ComparisonTable** `.lp-compare` (section `#why`): a real `<table>` with a hidden caption, column headers (Nima · Oddiy chatbot · GovAssist) and one row header per topic:
  - source;
  - office;
  - when unsure;
  - language;
  - freshness.

  The chatbot cells are muted, each with an `x` mark in a grey circle. The GovAssist cells sit on `--gradient-subtle`, each with a `check` mark in a brand-gradient circle.
  - < 768 px: each row becomes a card (topic, then the chatbot line, then the GovAssist line). Each line gets a small visible tag (`.lp-compare__tag`, `aria-hidden`, since the header cells still label the cells).
  - The claims describe only what the product does: cited official sources, the office from the directory, `not_found` instead of guessing, the four languages, the source fetch date.
- **ServiceTiles** `.lp-services` (section `#services`): 8 tiles, 2 columns on phones and 4 from 768 px.
  - Each tile `.lp-service` is one link: icon tile (primary on gradient-subtle) · title · example question · "Soʻrash →".
  - The tiles: passport/ID (`id-card`) · birth certificate (`baby`) · marriage (`heart-handshake`) · driving licence (`car`) · property (`house`) · business registration (`briefcase-business`) · pension (`hand-coins`) · utilities (`zap`).
  - Clicking carries the example question to sign-up, like the AskBox.
  - Titles and questions hyphenate (`hyphens: auto`) so long Russian words don't break mid-letter.
- **How it works** `.lp-steps` (`#how`), **FAQ** `.lp-faq` (`#faq`) and the **CTA band** `.lp-band` are as in v1.2. Each anchored section has `scroll-margin-top` so the sticky header doesn't cover its heading.
- **Footer** `.lp-footer`:
  - the brand column: wordmark, tagline, the long "not official" sentence, LanguageMenu (opens upwards);
  - then three columns, each with an `h2` title: **Mahsulot** (the four section links) · **Manbalar** (lex.uz and my.gov.uz as plain external text links, plus "Manbalar roʻyxati" → About) · **Huquqiy** (Loyiha haqida, Maxfiylik);
  - a bottom row: "© 2026 GovAssist" and the "Rasmiy davlat xizmati emas" pill `.lp-notofficial`;
  - the thesis line is removed;
  - phone: brand on top, then Product and Sources side by side, Legal full width.
- **CarriedQuestion** (Sign up): an info alert `[data-carried]` with "Savolingiz saqlandi", the question in `<q>`, and "Roʻyxatdan oʻtgach, javob shu savol bilan boshlanadi." It is hidden until a question is waiting.

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

v1.1 card rhythm: 20 px padding on phones, 24 px from 768 px, 16 px inside, 20 px between cards, `--shadow-1` on every card. Card headings carry their icon in a 36 px primary-subtle tile (`.card__head .icon`). Step numbers are filled primary circles (white on `#4642C8`, 7.31:1).

| Component | Class | Content (contract field) | Notes |
|---|---|---|---|
| AnswerHeader | `.answer-head` | kind label (`answer_type`), `title` (h2), `summary` (body-lg) | v1.1: the kind label is a primary-subtle pill with the compass (service) or scale (legal) icon; the title uses the h1 size and the summary full-strength text, so title + summary are read first |
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

---

## Icon inventory

Every icon is a real Lucide icon from **`lucide-static` 1.61.0**, copied unchanged into [`icons/`](icons/). In React, use **`lucide-react` 1.61.0** with the component name below. Don't add icons from any other set; the Google "G" (Button → "Continue with Google") is the only brand mark.

| Lucide name | `lucide-react` | Where it is used |
|---|---|---|
| `menu` | `Menu` | Top bar: open the history drawer; landing hamburger |
| `square-pen` | `SquarePen` | Top bar: new chat |
| `plus` | `Plus` | Sidebar and History: "Yangi suhbat" button |
| `arrow-up` | `ArrowUp` | InputBar: Send |
| `square` | `Square` | InputBar: Stop; ProgressLine stopped; "Javob toʻxtatildi" alert |
| `map-pin` | `MapPin` | OfficeCard heading, address row and map button; chat help list; landing step 3 |
| `phone` | `Phone` | OfficeCard call button and "phone unknown" row |
| `clock` | `Clock` | OfficeCard hours toggle and "hours unknown"; rate-limit and quota alerts; check-email rate limit |
| `external-link` | `ExternalLink` | Every external link: sources, map button, office "Manba" |
| `thumbs-up` | `ThumbsUp` | FeedbackBar 👍 |
| `thumbs-down` | `ThumbsDown` | FeedbackBar 👎 |
| `check` | `Check` | ProgressLine "sources found"; saved states; toasts; selected combobox option |
| `circle-check` | `CircleCheck` | Success alerts; verify and reset success; Turnstile placeholder |
| `x` | `X` | Drawer close; landing comparison: the chatbot mark |
| `triangle-alert` | `TriangleAlert` | Warning alerts (region fallback); invalid link; error page |
| `circle-alert` | `CircleAlert` | Field errors; danger alerts; chat error alerts |
| `info` | `Info` | Disclaimer; info alerts; About nav link |
| `chevron-down` | `ChevronDown` | Hours toggle; combobox |
| `chevron-left` | `ChevronLeft` | Onboarding "Orqaga" |
| `search` | `Search` | Combobox lead icon; not_found card |
| `trash-2` | `Trash2` | History delete; delete account; danger buttons |
| `settings-2` | `Settings2` | Settings nav link |
| `wifi-off` | `WifiOff` | Offline banner |
| `file-text` | `FileText` | Documents card; chat help list |
| `scale` | `Scale` | Legal kind label; "Qonunda nima deyilgan" card; chat help list |
| `building-2` | `Building2` | OfficeCard type label |
| `banknote` | `Banknote` | Fee tile |
| `hourglass` | `Hourglass` | Processing-time tile |
| `eye` | `Eye` | PasswordField "show" |
| `eye-off` | `EyeOff` | PasswordField "hide" (while the password is visible) |
| `mail` | `Mail` | Check email; reset link sent; prototype email notes |
| `log-out` | `LogOut` | Settings: log out |
| `message-square` | `MessageSquare` | Empty history; sign-up carried question |
| `refresh-cw` | `RefreshCw` | Retry; resend link; reload |
| `globe` | `Globe` | LanguageMenu button |
| `list-checks` | `ListChecks` | Steps card; chat help list; landing step 2 |
| `book-open` | `BookOpen` | Sources card; About source list |
| `compass` | `Compass` | Service kind label; off_topic card; 404 |
| `lock` | `Lock` | Privacy note; change password |
| `house` | `House` | 404 "Bosh sahifaga qaytish"; landing service tile: property |
| `id-card` | `IdCard` | Landing service tile: passport and ID card |
| `baby` | `Baby` | Landing service tile: birth certificate |
| `heart-handshake` | `HeartHandshake` | Landing service tile: marriage registration |
| `car` | `Car` | Landing service tile: driving licence |
| `briefcase-business` | `BriefcaseBusiness` | Landing service tile: business registration |
| `hand-coins` | `HandCoins` | Landing service tile: pension |
| `zap` | `Zap` | Landing service tile: utilities |
| `map-pin-x` | `MapPinX` | Landing problem: wrong office |
| `file-x` | `FileX` | Landing problem: a missing document |
| `clock-alert` | `ClockAlert` | Landing problem: outdated advice |
| `arrow-right` | `ArrowRight` | Landing AskBox "Soʻrash"; service tile "Soʻrash →" |
