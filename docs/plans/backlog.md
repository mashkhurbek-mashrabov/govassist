# Backlog (owned by the main session)

Follow-ups that are not blocking a merge. Each item names its source and the lane that owns it. Remove an item when its fix is merged.

## Backend (Jasur)

From Dilshod's review of PR #3 (2026-10-22). Line references are at a77ac16.

- [ ] **Assistant messages stuck as `streaming`** (`chat/service.py:252-268,456-461`). Create the user and assistant messages in one atomic call. Mark `streaming` rows older than the lock TTL as failed, at read time or with a management command.
- [ ] **N+1 queries on admin lists.** Add `list_select_related` to the chat, collector, offices, corpus and accounts admins.
- [ ] **Gemini clients built per request and never closed** (`chat/views.py:28-32`). Close them when the stream ends, or keep one client per event loop.
- [ ] **Geo cache ignores `ui_language`** (`geo/api/views.py:17-18`). Cache per language at the selector level.
- [ ] **Resend-verification abuse** (`accounts/services.py:65-67`). Apply allauth's per-email rate limit and send the email from a background task, so response time doesn't reveal whether an account exists.
- [ ] **Crawler robustness** (`collector/crawler.py:139-147`, `pipelines.py`):
  - one bad page must not abort the whole job;
  - no Gemini calls inside `transaction.atomic`;
  - an unreachable robots.txt means disallow (RFC 9309).
- [ ] **Dead code:** `LLMUnavailable` and `clean_working_hours` (or use it in `Office.clean()`).
- [ ] **WhiteNoise is sync-only**, so every request goes through a thread. Consider serving static files from nginx in prod.

## Frontend (Madina)

From Kamola's review of PR #2 (2026-10-22):

- [ ] **Onboarding field errors** (`OnboardingPage.tsx:102`). Map `problem.errors` on a 400 `validation_error` to the fields, so Save is never silent.
- [ ] **Stored `streaming` messages.** Poll or refetch while any stored assistant message is `streaming`, with a Retry after a timeout. Pairs with the backend item "stuck streaming rows".
- [ ] **Stale "writing" copy.** A follow-up asked before the post-answer refetch briefly shows the previous answer's stale "writing" copy.

## Evaluation (B6)

- [ ] **Honest normalization ablation.** `search(normalize=False)` only skips normalization on the query side, while the index stays transliterated. B6 needs a real "no normalization" index variant: a second `search_vector` over the raw text, or a separate index build. Otherwise the RQ3 normalization result is overstated.
