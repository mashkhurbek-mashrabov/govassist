# Screens

All 16 screens from `01-design-plan.md` §4. Each one links its prototype file. Every state has a screenshot `screenshots/<file>--<state>--375.png` and `--1440.png` (see the README for how they are made). Copy keys refer to [`copy.md`](copy.md); data fields refer to [`../contract.md`](../contract.md).

## Layouts

| Layout | Phone (< 768 px, designed at 375) | Tablet (768–1279) | Desktop (≥ 1280) |
|---|---|---|---|
| **Auth** (screens 1–6, 16) | Header (wordmark + language select) · one column, 16 px gutter · footer ("Rasmiy davlat xizmati emas", About, Privacy) | Same column, max 440 px, centred, more top space | Same as tablet |
| **App shell** (screens 7–15) | Sticky top bar 56 px: menu (opens the history drawer) · title · new chat. Full-width content, 16 px gutter. Sticky InputBar on chat screens | Same, 24 px gutter, headings one step larger | Permanent 296 px sidebar (wordmark, New chat, history, Settings, About, "not official") · centred column: chat max 760 px, other pages max 720 px · sticky InputBar aligned to the column |

---

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
- **Data:** the email comes from the signup/login response. **Resend has no endpoint in the contract** → README open question 1.

## 4. Verify email `/verify-email/:key` · [`verify-email.html`](prototype/verify-email.html)

- **States:** `verifying` (spinner, `role="status"`) · `success` ("Elektron pochta tasdiqlandi" → Continue to onboarding) · `invalid` (expired/invalid: Log in + "Yangi havola soʻrash").
- **Copy:** `verify.*`, `common.continue`.
- **Data:** POST `auth/email/verify` `{key}` on load.

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
- **States (in stream order):** `searching` (`status.stage=searching`) · `found` ("4 ta manba topildi", `source_count`) · `office` (the `office` event arrives before any `delta`: the office card renders complete under the header skeleton) · `summary` (title + summary growing with the caret; steps skeleton) · `steps` (steps 1–2 done, step 3 growing; skeleton for the next card) · `documents` (checklist done; fee/time skeleton tiles) · `stopped` (user pressed Stop: partial cards stay, stopped line). Final state = screen 9 `complete`.
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
- **States:** `stream-error` (`llm_unavailable`, Retry resends the same text) · `timeout` (`llm_timeout`) · `invalid` (`invalid_answer`) · `rate-limited` (429 `rate_limited`: "… {limit} tagacha … {minutes} daqiqadan soʻng …", input disabled until then) · `quota` (`quota_exceeded`) · `busy` (409 `stream_in_progress`) · `offline` (banner, input disabled) · `too-long` (counter over 1000, Send disabled).
- **Copy:** `chat_error.*`, `chat.too_long`, `common.retry`.
- **Data:** problem+json `code` and `retry_after` (minutes = ⌈retry_after / 60⌉); SSE `error.code`; `Me.quota.hour_limit`. `internal_error` uses `error.server`; a 401 anywhere shows `chat_error.session_ended` on the login screen.

## 13. History `/history` (phone) / sidebar (desktop) · [`history.html`](prototype/history.html)

- **Layout:** page title, New chat, list rows: `title` (semibold, one line), date + `last_message_preview` (one line, muted), delete IconButton. "Yana koʻrsatish" loads the next cursor page. A note explains `[PASSPORT]`-style markers. On desktop the same rows live in the sidebar (current conversation highlighted).
- **States:** `list` · `empty` · `loading` (skeleton rows) · `confirm` (delete dialog) · `deleting` (button spinner) · `deleted` (toast).
- **Copy:** `history.*`, `chat.new`, `common.today`, `common.yesterday`.
- **Data:** GET `/conversations` (cursor) → `ConversationSummary` (`id`, `title`, `updated_at` → "Bugun"/"Kecha"/`DD.MM.YYYY`, `last_message_preview`); DELETE `/conversations/{id}`.

## 14. Settings `/settings` · [`settings.html`](prototype/settings.html)

- **Layout:** cards: App language (select) · Your area (region + district comboboxes, Save) · Usage (two meters: hour and day) · Account (email, optional name, Change password, Log out, divider, Delete account).
- **States:** `default` · `saving` · `saved` · `confirm-delete` (dialog with an "I understand" checkbox that enables the danger button).
- **Copy:** `settings.*`, `onboarding.region`, `onboarding.district`, `common.save*`.
- **Data:** GET/PATCH `/me` (`ui_language`, `region`, `district`, `display_name`, `email`, `quota.hour_used/hour_limit/day_used/day_limit`); DELETE `/me` `{confirm: true}`; log out `DELETE auth/session`. **Change password** has no endpoint in the contract → open question 2.

## 15. About `/about` · [`about.html`](prototype/about.html)

- **Content:** "not an official government service" alert at the top · What is this · How answers are made (sources only, citations, offices from the database, not legal advice + the disclaimer) · Privacy (what is stored, PII scrubbing, Gemini, deleting the account) · Source list.
- **Copy:** `about.*`, `app.not_official_long`, `app.disclaimer`.
- **Data:** none from the API. The source list uses NAMUNA rows → open question 4.

## 16. 404 / generic error · [`404.html`](prototype/404.html)

- **States:** `not-found` (compass icon, "Sahifa topilmadi", Home) · `error` (error boundary: "Nimadir buzildi", Reload, Home).
- **Copy:** `notfound.*`, `error_page.*`.

---

## Extra review pages

- [`components.html`](prototype/components.html): every component and variant, including all office badges and InputBar states.
- [`type.html`](prototype/type.html): type scale, glyph proof, and the **long-string test set** (Russian and Uzbek Cyrillic strings for buttons, chips, office card, progress line, disclaimer and history) at 375 px.
