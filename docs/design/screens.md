# Screens

All 17 screens (0–16) from `01-design-plan.md` §4, then the end-to-end journeys J1–J6 (§4a). Each one links its prototype file. Every state has a screenshot `screenshots/<file>--<state>--375.png` and `--1440.png` (see the README for how they are made). Copy keys refer to [`copy.md`](copy.md); data fields refer to [`../contract.md`](../contract.md).

## Layouts

| Layout | Phone (< 768 px, designed at 375) | Tablet (768–1279) | Desktop (≥ 1280) |
|---|---|---|---|
| **Auth** (screens 0–6, 16) | Header (wordmark + language select) · one column, 16 px gutter · footer ("Rasmiy davlat xizmati emas", About, Privacy) | Same column, max 440 px, centred, more top space | Same as tablet |
| **App shell** (screens 7–15) | Sticky top bar 56 px: menu (opens the history drawer) · title · new chat. Full-width content, 16 px gutter. Sticky InputBar on chat screens | Same, 24 px gutter, headings one step larger | Permanent 296 px sidebar (wordmark, New chat, history, Settings, About, "not official") · centred column: chat max 760 px, other pages max 720 px · sticky InputBar aligned to the column |

---

## 0. Landing `/welcome` · [`welcome.html`](prototype/welcome.html)

- **Purpose:** first visit, before any account. Say in one sentence what GovAssist does, show what an answer looks like, and lead to Sign up.
- **Layout:** auth header (wordmark · language select · "Kirish" ghost link) · hero: display heading, lead, **Sign up** (primary) + **Log in** (secondary), "Savol berish uchun roʻyxatdan oʻting" note · a sample answer card (NAMUNA, from contract §6: kind label, title, 3 numbered steps with citation badges, office type + "Hozir ochiq" badge + address) · "Qanday ishlaydi": 3 cards (ask → get the steps & documents → go to the right office) · "not an official government service" note · footer (About, Privacy). Phone: one column, buttons full width. ≥ 768 px: buttons side by side, the 3 cards in a row. ≥ 1280 px: hero in two columns (text left, preview right), max 1152 px (`--layout-landing-max`).
- **States:** `default` · `ru` (same page with the Russian UI, the end of J6).
- **Copy:** `landing.*`, `app.not_official_long`.
- **Data:** none. The preview is static sample markup; its badges are not links.

## 1. Sign up `/signup` · [`signup.html`](prototype/signup.html)

- **Purpose:** create an account with email + password or Google, so the user can ask questions.
- **Components:** Button (google, primary block), divider-text, TextField, PasswordField with strength, Turnstile slot, Alert (danger), inline privacy note, links.
- **States:** `default` · `errors` (error summary, invalid email, weak/short password, Turnstile failed; also used for `error.email_taken` and `error.password_common`) · `submitting` (fields disabled, button spinner "Hisob yaratilmoqda…") · `server-error` (danger alert, form kept).
- **Copy:** `signup.*`, `auth.*`, `error.form_summary`, `error.email_invalid`, `error.email_taken`, `error.password_short`, `error.password_common`, `error.turnstile`, `error.server`.
- **Data:** POST `/_allauth/browser/v1/auth/signup` `{email, password, turnstile_token}`; Google via `auth/provider/redirect` (`provider=google`, `process=login`). allauth field errors map to the field errors above. Success → screen 3.

## 2. Log in `/login` · [`login.html`](prototype/login.html)

- **Components:** as signup, without strength or Turnstile; "Parolni unutdingizmi?" link.
- **States:** `default` · `wrong-credentials` (danger alert, values kept) · `social-error` (arriving at `/login?error=social`) · `submitting`.
- **Copy:** `login.*`, `auth.*`, `error.login_failed`, `error.social`.
- **Data:** POST `auth/login` `{email, password}`. Unverified email → screen 3; incomplete profile → screen 6.

## 3. Check your email `/check-email` · [`check-email.html`](prototype/check-email.html)

- **Layout:** centred state: mail icon, title, "{email} manziliga havola yubordik…", spam hint, then Resend (secondary) and "Boshqa elektron pochtadan foydalanish" (ghost → `/signup`).
- **States:** `sent` · `resent` (success alert) · `rate-limited` (warning alert "… {minutes} daqiqadan soʻng …", Resend disabled).
- **Copy:** `check_email.*`.
- **Data:** the email comes from the signup/login response. Resend: `POST /api/v1/auth/resend-verification` `{email}` → always `204`; `429 rate_limited` + `retry_after` → the rate-limited state. "Use a different email" goes back to `/signup` (there is no change-email endpoint).

## 4. Verify email `/verify-email/:key` · [`verify-email.html`](prototype/verify-email.html)

- **States:** `verifying` (spinner, `role="status"`) · `success` ("Elektron pochta tasdiqlandi" → Continue to onboarding) · `invalid` (expired/invalid: email field + "Yangi havola yuborish" → check-email `resent`; Log in link).
- **Copy:** `verify.*`, `common.continue`.
- **Data:** POST `auth/email/verify` `{key}` on load; the invalid state's form calls `POST /api/v1/auth/resend-verification` `{email}`.

## 5. Forgot / reset password · [`password.html`](prototype/password.html)

- **Routes:** `/forgot-password`, `/reset-password/:key`.
- **States:** `forgot` (email form) · `forgot-sent` (the same message whether or not the account exists, so emails can't be discovered) · `reset` (new password + strength) · `reset-invalid` · `reset-success` (→ Log in).
- **Copy:** `forgot.*`, `reset.*`, `auth.password_hint`.
- **Data:** POST `auth/password/request` `{email}`; POST `auth/password/reset` `{key, password}`.

## 6. Onboarding `/onboarding` · [`onboarding.html`](prototype/onboarding.html)

- **Purpose:** pick the UI language, then region → district, so the office lookup works.
- **Layout:** auth layout with a 2-step indicator. Step 1: four RadioCards (language names in their own script) + Next. Step 2: "Why we ask" info alert, Region combobox, District combobox (disabled until a region is chosen), "Saqlash va boshlash", Back.
- **States:** `language` · `place` (region list open, district disabled with reason) · `loading-districts` · `district-open` (filtering "Chil") · `validation` (district missing) · `saving`.
- **Copy:** `onboarding.*`, `lang.*`, `common.next`, `common.back`, `common.saving`.
- **Data:** GET `/geo/regions` → `[Region]`; GET `/geo/regions/{id}/districts` → `[District]`; PATCH `/me` `{ui_language, region_id, district_id}`; `profile_incomplete` (403) sends the user here. Lists show contract names plus NAMUNA placeholders.

## 7. Chat, empty `/` · [`chat-empty.html`](prototype/chat-empty.html)

- **Layout:** greeting (display size) and lead, "Masalan, soʻrang:" with 4 suggestion chips, "Nimalarda yordam beraman" card (4 rows with icons), sticky InputBar.
- **States:** `default` · `suggestions-loading` (chip skeletons) · `drawer` (phone: history drawer open over the scrim).
- **Copy:** `chat.greeting`, `chat.greeting_lead`, `chat.suggestions`, `chat.can_help`, `chat.help_1..4`, `chat.input_*`, `app.not_official`, `app.may_be_wrong`.
- **Data:** GET `/suggestions` → `items[].text` (≤ 6, all shown; chips wrap). `category` is not displayed.

## 8. Chat, answering · [`chat-streaming.html`](prototype/chat-streaming.html)

- **Layout:** user bubble → AssistantMessage that fills in; InputBar shows **Stop**.
- **States (in stream order):** `searching` (`status.stage=searching`) · `found` ("4 ta manba topildi", `source_count`) · `office` (the `office` event arrives before any `delta`: the office card renders complete under the header skeleton) · `summary` (title + summary growing with the caret; steps skeleton) · `steps` (steps 1–2 done, step 3 growing; skeleton for the next card) · `documents` (checklist done; fee/time skeleton tiles) · `stopped` (user pressed Stop: partial cards stay for this view only, stopped line). After a reload the message shows as screen 12 `stopped-reload`. Final state = screen 9 `complete`.
- **Copy:** `progress.*`, `chat.stop`.
- **Data:** SSE `meta`, `status`, `office`, `delta` (partial `Answer` JSON), `final`, `done` (contract §4).

## 9. Answer: service · [`answer-service.html`](prototype/answer-service.html)

- **Order:** AnswerHeader (`title`, `summary`) → StepsList (`steps`) → DocumentsChecklist (`documents`) → FactsRow (`fee`, `processing_time`) → **OfficeCard** (`office`) → LawPoints (only if `law_points` is not empty) → SourcesList (`sources`) → Disclaimer → FeedbackBar → FollowUpChips (`follow_up_questions`).
- **States:** `complete` · `partial` (some items have `source_ids: []` → no badge; S2 is then cited nowhere, so `sources` lists only S1) · `region` (`match=region` + alert) · `none` (`match=none`, `office=null`) · `no-office` (no card) · `unknown` (`working_hours: []`, `phone: null`) · `hours-open` (hours table expanded) · `feedback-down` (👎 pressed, comment open) · `feedback-saved` (👍 saved).
- **Copy:** `answer.*`, `office.*`, `day.*`, `feedback.*`, `app.disclaimer`.
- **Data:** `Message.answer` (all fields), `Message.sources` (`id`, `kind`, `title`, `publisher`, `url`, `section`, `published_at`, `fetched_at`), `Message.office` (`match`, `office_type.label`, `office.name`, `address`, `district.name`, `region.name`, `phone`, `working_hours`, `map_url`, `data_as_of`, `source_url`), `Message.feedback`. Not shown: `office.id`, `latitude`/`longitude` (already inside `map_url`), `answer.language` (used only for `lang` on the answer container).

## 10. Answer: legal · [`answer-legal.html`](prototype/answer-legal.html)

- **Order:** AnswerHeader (kind "Huquqiy savol") → "Qonunda nima deyilgan": LawPointCards (quote block + "Oddiy tilda" explanation + badge; the article/section reference comes from the cited source's `section`, e.g. "12-band", in the sources list) → "Nima qilishingiz mumkin" (`steps`) → SourcesList → Disclaimer → FeedbackBar → FollowUpChips.
- **States:** `complete` (the second law point has no citation, to show the no-badge case).
- **Data:** `answer_type=legal`, `law_points[]`, `steps[]`, `sources[]`. All text is NAMUNA (the contract has no legal example).

## 11. Answer: not found / off topic · [`answer-not-found.html`](prototype/answer-not-found.html)

- **Layout:** one card: icon + `title` (h2), `summary`, a static help line, topic chips; then the Disclaimer (always present) and FeedbackBar.
- **States:** `not-found` (help: "Savolni boshqa soʻzlar bilan…") · `off-topic` (help: "Men davlat xizmatlari va … javob beraman").
- **Data:** `answer_type`, `title`, `summary`, `follow_up_questions` (used as chips when present; otherwise `/suggestions`).

## 12. Chat errors · [`chat-errors.html`](prototype/chat-errors.html)

- **Layout:** an inline alert in place of the assistant message, under the user bubble; offline uses a banner under the top bar.
- **States:** `stream-error` (`llm_unavailable`, Retry resends the same text) · `timeout` (`llm_timeout`) · `invalid` (`invalid_answer`) · `rate-limited` (429 `rate_limited`: "… {limit} tagacha … {minutes} daqiqadan soʻng …", input disabled until then) · `stopped-reload` (a stored message with `status: failed`, `error_code: "stopped"`: "Javob toʻxtatildi" + Retry) · `quota-user` (`quota_exceeded`, `scope: "user"`: ask again tomorrow) · `quota-global` (`scope: "global"`: the service's overall daily limit) · `busy` (409 `stream_in_progress`) · `offline` (banner, input disabled) · `back-online` (banner gone, toast "Aloqa tiklandi") · `too-long` (counter over 1000, Send disabled).
- **Copy:** `chat_error.*`, `chat.too_long`, `common.retry`.
- **Data:** problem+json `code`, `retry_after` (minutes = ⌈retry_after / 60⌉) and `scope`; SSE `error.code` / `error.scope`; stored `Message.error_code` after a reload; `Me.quota.hour_limit`. `internal_error` uses `error.server`; a 401 anywhere shows `chat_error.session_ended` on the login screen.

## 13. History `/history` (phone) / sidebar (desktop) · [`history.html`](prototype/history.html)

- **Layout:** page title, New chat, list rows: `title` (semibold, one line), date + `last_message_preview` (one line, muted), delete IconButton. "Yana koʻrsatish" loads the next cursor page. A note explains `[PASSPORT]`-style markers. On desktop the same rows live in the sidebar (current conversation highlighted).
- **States:** `list` · `empty` · `loading` (skeleton rows) · `confirm` (delete dialog) · `deleting` (button spinner) · `deleted` (toast).
- **Copy:** `history.*`, `chat.new`, `common.today`, `common.yesterday`.
- **Data:** GET `/conversations` (cursor) → `ConversationSummary` (`id`, `title`, `updated_at` → "Bugun"/"Kecha"/`DD.MM.YYYY`, `last_message_preview`); DELETE `/conversations/{id}`.

## 14. Settings `/settings` · [`settings.html`](prototype/settings.html)

- **Layout:** cards: App language (select; the UI switches at once) · Your area (region + district comboboxes, Save) · Usage (two meters: hour and day) · Account (email, optional name, Change password / Set a password, Log out, divider, Delete account). Change password opens an inline form in the Account card: current password (hidden when `has_password` is false) + new password with strength, Save / Cancel.
- **States:** `default` · `saving` · `saved` · `password` (form open) · `password-error` ("Joriy parol notoʻgʻri") · `password-saving` · `password-saved` (success alert) · `google` (`has_password: false`: "Parol oʻrnatish" with a short explanation, no current-password field) · `ru` (UI language switched to Russian; region/district names come back localized) · `confirm-delete` (dialog with an "I understand" checkbox that enables the danger button).
- **Copy:** `settings.*`, `onboarding.region`, `onboarding.district`, `common.save*`.
- **Data:** GET/PATCH `/me` (`ui_language`, `region`, `district`, `display_name`, `email`, `quota.hour_used/hour_limit/day_used/day_limit`); DELETE `/me` `{confirm: true}`; log out `DELETE auth/session` → `/welcome`. Change / set password: `POST /_allauth/browser/v1/account/password/change` `{current_password, new_password}`, omitting `current_password` when `Me.has_password` is false.

## 15. About `/about` · [`about.html`](prototype/about.html)

- **Content:** "not an official government service" alert at the top · What is this · How answers are made (sources only, citations, offices from the database, not legal advice + the disclaimer) · Privacy (what is stored, PII scrubbing, Gemini, deleting the account) · Source list.
- **Copy:** `about.*`, `app.not_official_long`, `app.disclaimer`.
- **Data:** the source list is `GET /api/v1/sources` → `items[]` `SourceSummary`: `name` (external link to `url`), `publisher` · kind label (`law` / `service_page` / `office` / `other`) · "{documents} ta hujjat" · "Yangilangan: {last_fetched_at}". Rows are NAMUNA; the first is the contract example.

## 16. 404 / generic error · [`404.html`](prototype/404.html)

- **States:** `not-found` (compass icon, "Sahifa topilmadi", Home) · `error` (error boundary: "Nimadir buzildi", Reload, Home).
- **Copy:** `notfound.*`, `error_page.*`.

---

## End-to-end journeys J1–J6 · [`journeys.html`](prototype/journeys.html)

Each journey is one file (`j1.html` … `j6.html`); every step is a `<section class="flow-step">` and the URL hash names the step, so any step can be linked. [`prototype/flow.js`](prototype/flow.js) wires the primary actions (`href="#step"`, `data-go`, form submits with a short busy state), plays the streaming steps on a timer, types the growing text, and drives the bar at the top (step n of N, Back, **Pause**, Next). With reduced motion the steps still advance, but the text appears at once (the stages jump). `?shot` freezes a step for screenshots. Every step is in `screenshots/journeys/` (`J1-01-landing.png` …; J2 and J6 also at 1440).

| # | Steps | Path (content is NAMUNA except contract §6) |
|---|---|---|
| J1 | 23 | Landing → Sign up → Check email (prototype note opens the email link) → Verifying → Verified → Onboarding language → region/district → Chat empty → tap "Pasportimni qanday yangilayman?" → streaming: searching → found → **office card early** → summary → steps → documents → fee/time → final → 👍 saved → tap the follow-up chip → **second turn in the same thread** (short service answer, no office) streams → final |
| J2 | 11 | Landing → Log in → chat with history (desktop sidebar) → New chat with the uz-Cyrl labour-law question typed → streaming: searching → found → summary → law points → "what you can do" → **legal answer** (two law points: quote + plain explanation + badges; Cyrillic content, uz-Latn UI) → tap badge 1 → source highlighted (opens lex.uz) |
| J3 | 9 | Russian question typed → streaming → office card `match=region` with unknown hours arrives early → **Russian service answer** (one document uncited, processing time not stated) → "Google Xaritada ochish" opens Maps in a new tab |
| J4 | 14 | Off-topic question → `off_topic` card with topic chips → tap a topic → `not_found` card → rephrased question typed → service answer with an FHDYo office in the lunch break |
| J5 | 18 | Question → streaming → **Stop** → partial cards + "Javob toʻxtatildi" → reload → stored `error_code: "stopped"` with Retry → Retry streams → final → next question → `rate_limited` (21 min) → `quota_exceeded` `scope=user` → `scope=global` → offline banner → back online |
| J6 | 16 | History → open an old chat → history → delete "NAMUNA suhbat 3" → confirm → deleted toast → Settings → switch to Русский (UI updates) → change password → saved → Log out → Russian landing. Then Log in → Forgot password → sent → reset → success → Log in |

Rules the journeys follow: every primary action leads to the next step (checked by `shoot.cjs`: no dead ends, no link to a missing step); states with no in-app action (an email arriving, a reload, the next limit state) carry a dashed **Prototype** note with the link. The UI language is the user's `ui_language` (uz-Latn) while answer content follows the question's script (`answer.language`), as in J2 and J3; only J6 switches the UI itself.

## Extra review pages

- [`components.html`](prototype/components.html): every component and variant, including all office badges and InputBar states.
- [`type.html`](prototype/type.html): type scale, glyph proof, and the **long-string test set** (Russian and Uzbek Cyrillic strings for buttons, chips, office card, progress line, disclaimer and history) at 375 px.
