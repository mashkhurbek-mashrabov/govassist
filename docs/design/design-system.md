# GovAssist design system v1.3

Foundations for every screen. Values live in [`tokens.css`](tokens.css) (source) and [`tokens.json`](tokens.json) (derived). This page explains them; it never redefines them.

## 1. Principles

1. **Clarity over decoration.** One primary action per screen. Plain words, short lines, no imagery.
2. **Trust is visible.** Facts carry citation badges. Office cards show "Maʼlumot … holatiga" and a source link. The disclaimer sits under every answer.
3. **Calm and neutral, not official.** No state emblem, no flag colours (blue/white/green/red bands), no my.gov.uz look. The brand is the **GovAssist** wordmark with the author's mark (a speech bubble that ends in a map pin, with a check; indigo to violet gradient; see components.md, Logo). "Rasmiy davlat xizmati emas" appears under the chat input, in the sidebar, in every auth footer and on About.
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
| `--text-display-xl-*` (v1.2) | 40 px | 60 px | 1.1 | Landing headline only, −0.025 em tracking (`--letter-spacing-tighter`) |
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

Page gutter `--layout-gutter`: 16 px on phones, 24 px from 768 px. Content widths: chat 760 px, settings/about 720 px, auth 440 px, landing 1152 px, landing FAQ 720 px (`--layout-prose-narrow`).

Component sizes added in v1.2: `--size-lang-code` (2.5ch, fixed width of the UZ / ЎЗ / RU / EN code in the sidebar's block language button; the compact button is globe-only since v1.3), `--size-popover` (256 px, language popover), `--size-lang-card` (72 px, minimum height of a language card). `--z-popover` (35) puts the popover and the phone sheet above the sticky header and below dialogs. Card padding 16 px on phones, 20/24 px from 768 px. Gap between answer cards 16 px; between messages 24 px.

## 5. Radius (3 steps)

| Token | Value | Use |
|---|---|---|
| `--radius-sm` | 8 px | Badges, citation badges, list options, skeleton bars |
| `--radius-md` | 12 px | Buttons, inputs, alerts, card-header icon tiles |
| `--radius-lg` | 20 px | Cards, message bubbles, dialogs, chips, InputBar, kind pill |

(v1.1 raised all three steps by 2–4 px for a softer, friendlier look.)

## 6. Elevation (2 levels)

| Token | Use |
|---|---|
| `--shadow-1` | Content cards, chips, InputBar (v1.1: every card lifts slightly off the page wash) |
| `--shadow-2` | Dialogs, drawer, open combobox list, toast |

Two helper shadows: `--shadow-glass` (the soft drop under glass bars) and `--shadow-primary` (an indigo glow that makes primary buttons and Send the obvious action). Dividers and card edges stay a 1 px `--color-border`.

## 7. Motion

| Token | Value | Use |
|---|---|---|
| `--motion-duration-fast` | 120 ms | Hover, chevron rotate |
| `--motion-duration-base` | 200 ms | Drawer, toast |
| `--motion-duration-slow` | 320 ms | Source highlight fade |
| `--motion-duration-pulse` | 1200 ms | Progress dots, skeleton shimmer, spinner, typing caret |
| `--motion-ease-standard` | cubic-bezier(0.2, 0, 0, 1) | Entering, state changes |
| `--motion-ease-exit` | cubic-bezier(0.4, 0, 1, 1) | Leaving |
| `--motion-press-scale` | 0.98 | Buttons, chips and icon buttons shrink slightly while pressed |
| `--motion-duration-preview` (v1.2) | 9000 ms | One play of the landing's streaming-answer preview (it plays once and holds) |

**Micro-interactions (v1.1):** press scale on buttons, chips and icon buttons; chips lift 2 px on hover; each new answer block fades and rises 8 px into place (`rise-in`, `--motion-duration-slow`) as it streams in. All of them are removed under reduced motion.

**v1.2:** the language popover scales in from 96 % and the phone sheet slides up (`--motion-duration-base`); switching language fades the content to 35 % and back (200 ms); the landing preview reveals its blocks in order. Under reduced motion all of them are instant and the preview shows the finished card.

**Reduced motion** (`prefers-reduced-motion: reduce`): `tokens.css` sets every duration to 0 ms, and components switch animations off (`animation: none`). The progress line still shows the stage **text**, the dots stay solid, the skeleton is a flat grey bar and the caret stays still. Nothing slides; the drawer and toast simply appear. All screenshots were taken with reduced motion on, so they show the reduced variant.

## 8. Icons

**One package: Lucide, pinned to `lucide-static` 1.61.0** (ISC licence, [lucide.dev](https://lucide.dev)). The frontend uses **`lucide-react` 1.61.0**, the same version, so names and shapes match exactly.

- The exact SVG files are copied unchanged into [`icons/`](icons/) (51 icons + `LICENSE.txt`). The prototype inlines their children verbatim; nothing is redrawn.
- `node docs/design/tokens.mjs --check` fails if any inline icon in the prototype differs from a file in `icons/`. The Google "G" is the one non-Lucide mark (class `icon--brand`, see components.md → Button).
- Drawing: 24 px grid, 2 px stroke, round caps and joins, `currentColor`, shown at 20 px (`--size-icon`), 16 px (`--size-icon-sm`) or 24 px (`--size-icon-lg`).
- Every icon is either next to a visible label (and `aria-hidden="true"`) or inside an icon button with an `aria-label`.
- The full name → where-used inventory, with the `lucide-react` component names, is in [`components.md`](components.md#icon-inventory).
- To add an icon: copy it from the same `lucide-static` version into `icons/`, add it to the inventory, and use the same name in React.

## 8b. Gradients and depth (v1.1)

The author asked for a prettier, more professional look with "a little bit gradient". All gradients use **two close hues (indigo → violet)** at low contrast, are tokens, and keep text AA at both ends.

| Token | Stops | Where | Text on it (worst end) |
|---|---|---|---|
| `--gradient-brand` | indigo-600 `#4642C8` → violet-600 `#5B3FD1` | Primary buttons, Send, logo mark, step numbers, office-card edge | white 6.83 |
| `--gradient-brand-hover` | indigo-700 → violet-700 `#4A2FB0` | Hover/pressed primary | white 9.03 |
| `--gradient-subtle` | indigo-50 → violet-50 `#F3EFFF` | Active nav item, current chat, checked radio card, kind pill, user bubble, chip hover | indigo-700 8.40 |
| `--gradient-text` | indigo-800 `#2C287F` → violet-700 | Landing and greeting headlines (gradient-clipped text) | 8.65 on the page, 8.2 on the hero |
| `--gradient-hero` | indigo-50 → violet-50 → white | Landing hero panel, chat greeting panel | body text 15+, muted 6.7 |
| `--gradient-card` | white → neutral-50 | Content cards (a barely visible lift) | unchanged |
| `--gradient-mesh` (v1.2) | radial blobs of indigo-200 `#C3C8FA`, violet-100, indigo-100 and amber-50 over indigo-50 → white | Landing hero only | at the darkest point (indigo-200): text 10.79, muted 4.71, headline gradient 7.55 / 5.58 |
| `--gradient-page` | indigo-100, violet-100, amber-50 radial washes | Fixed page backdrop behind the glass | muted 6.03 at the darkest point |

Gradient headline text falls back to plain `CanvasText` under `forced-colors: active`. Only one element per screen uses gradient text.

**Depth:** `--shadow-1` and `--shadow-2` are now three-layer shadows (a crisp 1–2 px contact shadow, a soft mid shadow and a wide ambient shadow), and `--shadow-primary` adds a violet-tinted glow under primary actions. Card edges use the softer `--color-border-subtle` (stone at 7 %); the office card alone gets a 1 px brand-gradient edge (gradient border-box under a solid padding-box), so the place to go stands out.

## 8a. Glass surfaces (v1.1)

Frosted glass (translucent fill + `backdrop-filter: blur() saturate()` + hairline border + 1 px top highlight) on the **floating chrome only**: top bar, sticky composer, desktop sidebar, mobile drawer, dialogs and toasts. Content cards (answers, office card, forms) stay **solid white** for reading. The office-card header (optional in the plan) stays solid, so the card that matters most has no transparency.

| Token | Light | Dark (provisional) | Use |
|---|---|---|---|
| `--color-glass` | white, α 0.82 | stone-900, α 0.88 | Bars, composer, sidebar, drawer |
| `--color-glass-strong` | white, α 0.90 | stone-900, α 0.92 | Dialogs and toasts (they sit on the scrim) |
| `--color-glass-border` | stone-950, α 0.08 | white, α 0.08 | Hairline edge |
| `--color-glass-highlight` | white, α 0.70 | white, α 0.06 | 1 px inner top highlight |
| `--glass-blur` | 14 px | 14 px | Modest, so low-end Android stays smooth |
| `--glass-saturate` | 1.4 | 1.4 | Keeps colours behind the glass lively |
| `--shadow-glass` | soft 4/16 px drop | — | Under the composer |
| `--gradient-page` | three soft radial washes (indigo-100, amber-50, indigo-50) | — | Fixed page backdrop, so the glass has colour to frost |

The page wash is painted on a fixed `body::before` layer. It stays behind the glass while content scrolls and is composited once, which is cheaper than `background-attachment: fixed`. Only six surfaces are glass, and never two stacked except the dialog over the scrim, so blur stays affordable.

**Contrast on glass (worst case).** The glass alphas were chosen so text passes AA even if **solid** dark content (`#1C1917` text, worst case) sits right behind the bar; blur only makes the real backdrop lighter. Computed by alpha-compositing the glass over each worst-case colour:

| Text on glass | Worst-case backdrop | Composite | Ratio | Need |
|---|---|---|---|---|
| Text `#1C1917` on `--color-glass` | solid `#1C1917` | `#D6D6D5` | 12.02 | 4.5 |
| Muted `#57534E` on `--color-glass` | solid `#1C1917` | `#D6D6D5` | 5.25 | 4.5 |
| Link `#4642C8` on `--color-glass` | solid `#1C1917` | `#D6D6D5` | 5.02 | 4.5 |
| Muted on `--color-glass` | primary button `#4642C8` | `#DEDDF5` | 5.73 | 4.5 |
| Muted on `--color-glass-strong` | scrim over dark text | `#E8E7E7` | 6.18 | 4.5 |
| Dark theme: muted `#A8A29E` on `--color-glass` | solid white content | — | 4.84 | 4.5 |
| Muted on the page wash (darkest point, indigo-100) | — | `#E0E3FF` | 6.03 | 4.5 |
| Input border `#78716C` on the page wash | — | `#E0E3FF` | 3.79 | 3 |

**Solid fallbacks.** Two blocks in `tokens.css` swap the glass tokens to opaque white and the blur to 0: `@supports not (backdrop-filter: blur(1px))` and `@media (prefers-reduced-transparency: reduce)`. Both use the same values. Screenshots of each, next to the glass version, are in [`screenshots/glass/`](screenshots/glass/). The reduced-transparency shots use real media emulation; the no-`backdrop-filter` shots apply the same token values with `backdrop-filter` removed.

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
