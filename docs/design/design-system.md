# GovAssist design system v1

Foundations for every screen. Values live in [`tokens.css`](tokens.css) (source) and [`tokens.json`](tokens.json) (derived). This page explains them; it never redefines them.

## 1. Principles

1. **Clarity over decoration.** One primary action per screen. Plain words, short lines, no imagery.
2. **Trust is visible.** Facts carry citation badges. Office cards show "Maʼlumot … holatiga" and a source link. The disclaimer sits under every answer.
3. **Calm and neutral, not official.** No state emblem, no flag colours (blue/white/green/red bands), no my.gov.uz look. The brand is a plain **GovAssist** wordmark with a neutral speech-bubble mark. "Rasmiy davlat xizmati emas" appears under the chat input, in the sidebar, in every auth footer and on About.
4. **Accessible by default.** WCAG 2.2 AA; see §9.
5. **Phone-first.** Designed at 375 px, then 768 px and 1280 px+.
6. **Fast.** Self-hosted Inter, two weights, about 160 KB of WOFF2 for all four subsets (the browser downloads only the subsets a page uses). No images, no icon font.

## 2. Typography

**Family:** Inter 5.3.0 (SIL OFL 1.1), self-hosted from [`fonts/`](fonts/) via [`fonts/inter.css`](fonts/inter.css). Fallback: `system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif`.

Glyph check (proof: [`screenshots/glyph-proof.png`](screenshots/glyph-proof.png), [`prototype/type.html`](prototype/type.html)):

| Need | Glyphs | Inter subset |
|---|---|---|
| Uzbek Latin | oʻ gʻ Oʻ Gʻ (U+02BB), maʼlumot (U+02BC) | `latin` (range includes U+02BB–02BC) |
| Uzbek Cyrillic | ў Ў (U+045E/040E) | `cyrillic` |
| Uzbek Cyrillic | қ ғ ҳ Қ Ғ Ҳ (U+049B, U+0493, U+04B3…) | `cyrillic-ext` |
| Russian | full Cyrillic | `cyrillic` |

Playwright confirmed `document.fonts.check("16px Inter", …)` is true for both sets and that the `latin`, `cyrillic` and `cyrillic-ext` faces load (400 and 600).

**Weights:** 400 (regular) and 600 (semibold) only.

| Token | Mobile | ≥ 768 px | Line height | Use |
|---|---|---|---|---|
| `--text-display-*` | 28 px | 36 px | 1.25 | Chat greeting |
| `--text-h1-*` | 24 | 30 | 1.3 | Page titles |
| `--text-h2-*` | 20 | 22 | 1.35 | Answer title, sections |
| `--text-h3-*` | 18 | 19 | 1.4 | Card headings, office name |
| `--text-body-lg-*` | 18 | 18 | 1.55 | Answer summary, quotes |
| `--text-body-*` | **16** | 16 | 1.5 | All body copy (minimum) |
| `--text-small-*` | 14 | 14 | 1.45 | Meta only: hints, dates, source meta |
| `--text-caption-*` | 13 | 13 | 1.4 | Badge labels, counters |

Rules: sizes are in `rem`, so 200 % zoom scales everything. Body copy never goes below 16 px. Headings use −0.01 em tracking. Long words break (`overflow-wrap: anywhere`) so a long Russian compound never pushes the layout wider than 375 px.

## 3. Colour

A warm-neutral base (stone) with one accent: **indigo** (`--palette-indigo-600 #4642C8`). It is calm and reads as trustworthy, and it is clearly not the flag's sky blue or green or my.gov.uz's blue. Semantic colours: success green, warning amber, danger red, info = indigo.

Components use **only** the semantic layer (`--color-*`). The palette (`--palette-*`) exists to feed it. A theme overrides the semantic layer only; `:root[data-theme="dark"]` is a provisional dark theme that proves the structure (contrast checked below, not yet design-reviewed).

| Semantic token | Light value | Role |
|---|---|---|
| `--color-bg` | neutral-50 | Page |
| `--color-surface` | white | Cards, inputs, top bar, sidebar |
| `--color-surface-sunken` | neutral-100 | Disclaimer, quotes, hover |
| `--color-text` / `-muted` | neutral-900 / neutral-600 | Text |
| `--color-border` | neutral-200 | Decorative dividers and card edges |
| `--color-border-strong` | neutral-500 | Input and secondary-button borders (≥ 3:1) |
| `--color-primary` (+ `-hover`, `-active`) | indigo-600/700/800 | Primary buttons, links, focus ring |
| `--color-primary-subtle` (+ `-border`, `on-`) | indigo-50/200/700 | Citation badges, chips, user bubble, selection |
| `--color-success*` / `--color-open*` | green | "Hozir ochiq" |
| `--color-warning*` / `--color-break*` | amber | Lunch break, region fallback, rate limits, offline |
| `--color-danger*` / `--color-closed*` | red | Errors, "Yopiq", destructive actions |
| `--color-google-*` | Google brand | Only the "G" mark on the Google button (brand rules) |

### Contrast table (WCAG 2.2, computed from the token hex values)

Text needs 4.5:1; UI parts (borders, focus ring, icons that carry meaning) need 3:1.

| Pair | FG | BG | Ratio | Need | Result |
|---|---|---|---|---|---|
| Text on surface | #1C1917 | #FFFFFF | 17.49 | 4.5 | Pass |
| Text on page | #1C1917 | #FAFAF9 | 16.74 | 4.5 | Pass |
| Muted text on surface | #57534E | #FFFFFF | 7.63 | 4.5 | Pass |
| Muted text on page | #57534E | #FAFAF9 | 7.30 | 4.5 | Pass |
| Muted text on sunken (disclaimer) | #57534E | #F5F5F4 | 6.99 | 4.5 | Pass |
| Link on surface | #4642C8 | #FFFFFF | 7.31 | 4.5 | Pass |
| Link hover | #3833A8 | #FFFFFF | 9.51 | 4.5 | Pass |
| Primary button text | #FFFFFF | #4642C8 | 7.31 | 4.5 | Pass |
| Primary button hover | #FFFFFF | #3833A8 | 9.51 | 4.5 | Pass |
| Citation badge / chip hover | #3833A8 | #EEF0FF | 8.40 | 4.5 | Pass |
| Chip text on surface | #3833A8 | #FFFFFF | 9.51 | 4.5 | Pass |
| User bubble text | #1C1917 | #EEF0FF | 15.44 | 4.5 | Pass |
| "Hozir ochiq" badge | #166534 | #F0FDF4 | 6.81 | 4.5 | Pass |
| Lunch-break badge | #92400E | #FFFBEB | 6.84 | 4.5 | Pass |
| "Yopiq" badge | #B91C1C | #FEF2F2 | 5.91 | 4.5 | Pass |
| Field error text, danger-ghost button | #B91C1C | #FFFFFF | 6.47 | 4.5 | Pass |
| Danger button text | #FFFFFF | #B91C1C | 6.47 | 4.5 | Pass |
| Text on danger alert | #1C1917 | #FEF2F2 | 15.99 | 4.5 | Pass |
| Text on warning alert / banner | #1C1917 | #FFFBEB | 16.86 | 4.5 | Pass |
| Input border vs surface | #78716C | #FFFFFF | 4.80 | 3 | Pass |
| Input border vs page | #78716C | #FAFAF9 | 4.59 | 3 | Pass |
| Focus ring vs page | #4642C8 | #FAFAF9 | 7.00 | 3 | Pass |
| Focus ring vs surface | #4642C8 | #FFFFFF | 7.31 | 3 | Pass |
| Step number / progress dots | #4642C8 | #EEF0FF | 6.45 | 3 | Pass |
| Invalid input border | #B91C1C | #FFFFFF | 6.47 | 3 | Pass |
| Disabled text (exempt, WCAG 1.4.3) | #78716C | #F5F5F4 | 4.40 | — | Exempt |

Dark theme (provisional): text 16.03, muted 6.93, link 8.11, primary button 8.17, citation 10.87, open 9.19, break 10.18, closed 8.54 (all ≥ 4.5); input border 3.65 and focus ring 9.17 (≥ 3). All pass.

Colour is never the only signal: badges carry text ("Hozir ochiq", "Yopiq"), errors carry an icon and text, the selected option carries a check mark.

## 4. Spacing

4 px base: `--space-1` (4) · `-2` (8) · `-3` (12) · `-4` (16) · `-5` (20) · `-6` (24) · `-8` (32) · `-10` (40) · `-12` (48) · `-16` (64). `--space-half` (2) is for optical icon nudges only.

Page gutter `--layout-gutter`: 16 px on phones, 24 px from 768 px. Content widths: chat 760 px, settings/about 720 px, auth 440 px, landing 1152 px. Card padding 16 px on phones, 20/24 px from 768 px. Gap between answer cards 16 px; between messages 24 px.

## 5. Radius (3 steps)

| Token | Value | Use |
|---|---|---|
| `--radius-sm` | 6 px | Badges, citation badges, list options, skeleton bars |
| `--radius-md` | 10 px | Buttons, inputs, alerts |
| `--radius-lg` | 16 px | Cards, message bubbles, dialogs, chips, InputBar |

## 6. Elevation (2 levels)

| Token | Use |
|---|---|
| `--shadow-1` | Office card (the one card that must stand out), raised cards |
| `--shadow-2` | Dialogs, drawer, open combobox list, toast |

Everything else is flat with a 1 px `--color-border`.

## 7. Motion

| Token | Value | Use |
|---|---|---|
| `--motion-duration-fast` | 120 ms | Hover, chevron rotate |
| `--motion-duration-base` | 200 ms | Drawer, toast |
| `--motion-duration-slow` | 320 ms | Source highlight fade |
| `--motion-duration-pulse` | 1200 ms | Progress dots, skeleton shimmer, spinner, typing caret |
| `--motion-ease-standard` | cubic-bezier(0.2, 0, 0, 1) | Entering, state changes |
| `--motion-ease-exit` | cubic-bezier(0.4, 0, 1, 1) | Leaving |

**Reduced motion** (`prefers-reduced-motion: reduce`): `tokens.css` sets every duration to 0 ms, and components switch animations off (`animation: none`). The progress line still shows the stage **text**, the dots stay solid, the skeleton is a flat grey bar and the caret stays still. Nothing slides; the drawer and toast simply appear. All screenshots were taken with reduced motion on, so they show the reduced variant.

## 8. Icons

[Lucide](https://lucide.dev) outline set (ISC licence; the frontend uses `lucide-react`): 24 px grid, 2 px stroke, round caps, drawn at 20 px (`--size-icon`) or 24 px. The prototype inlines the SVG paths. Every icon is either next to a visible label (and `aria-hidden="true"`) or inside an icon button with an `aria-label`.

Used: menu, square-pen (new chat), plus, arrow-up (send), square (stop), map-pin, phone, clock, external-link, thumbs-up/down, check, circle-check, x, triangle-alert, circle-alert, info, chevron-down/left, search, trash-2, settings-2, wifi-off, file-text, scale, building-2, banknote, hourglass, eye, mail, log-out, message-square, refresh-cw, globe, list-checks, book-open, compass, lock, house.

## 9. Accessibility rules

- **Contrast:** §3 table. Text ≥ 4.5:1, UI ≥ 3:1.
- **Targets ≥ 44 × 44 px** (`--size-touch-min`) for every button, link-button, input, option, summary and chip. Inputs and primary buttons are 48 px (`--size-control`). Citation badges look 24 px but have a 44 px hit area (`::after`), with 12 px between badges so hit areas don't overlap. Inline text links inside sentences use the WCAG 2.5.8 inline exception. Playwright measured every interactive element on every screen at both sizes: no target under 44 px.
- **Focus:** 3 px `--color-focus-ring` outline, 2 px offset, on `:focus-visible`. The InputBar shows the ring on the whole bar (`:focus-within`).
- **Zoom/reflow:** `rem` sizes, no fixed heights on text containers, `overflow-wrap: anywhere`. No horizontal scroll at 375 px on any screen (checked by script). 200 % zoom on a 768 px window gives a 384 px CSS viewport, so it uses the phone layout that was checked.
- **Structure:** one `h1` per page; landmarks `header` / `nav` / `main` / `aside` / `footer`; a skip link; answer sections are `section` + heading; steps are an `ol`, sources an `ol` whose numbers match the badges.
- **Live regions:** the progress line is `role="status"` `aria-live="polite"` and announces stage changes, not deltas. Errors that block the user use `role="alert"`. The answer container has `aria-busy="true"` while streaming.
- **Forms:** visible labels, hints and errors linked with `aria-describedby`, `aria-invalid` on bad fields, an error summary at the top, `autocomplete` on email/password.
- **Dialogs:** `role="alertdialog"`, `aria-modal`, focus trapped and returned, Esc closes, Cancel listed first in the DOM.
- **Language:** `<html lang>` follows the UI language (`uz-Latn`, `uz-Cyrl`, `ru`, `en`); mixed-script snippets get their own `lang`.
- **Automated check:** axe-core (WCAG 2.0/2.1/2.2 A + AA rules) on every screen at 375 px: **0 serious or critical violations**.
