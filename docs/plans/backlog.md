# Backlog (owned by the main session)

Follow-ups that are not blocking a merge. Each item names its source and the lane that owns it. Remove an item when its fix is merged.

## Backend (Jasur)

Items 1–7 from Dilshod's review were fixed in PR #18 (2026-10-23).

- [ ] **WhiteNoise is sync-only**, so every request goes through a thread. Consider serving static files from nginx in prod.

## Integration (main session, G4)

- [ ] **Google login end to end:** the callback route is mounted (#8) and `/accounts` is proxied (PR #7). Still to do: test a real Google sign-in once the author's OAuth client is in `.env`.
- [ ] Add the `web` service to compose (build `frontend/`, target runtime), passing `VITE_TURNSTILE_SITE_KEY` as a **build arg**, because the build fails without it. Use Cloudflare's test key in dev.
- [ ] Upstream the generic auth rate-limit string from `frontend/src/i18n/extra-copy.json` into `docs/design/copy.md`.

## Evaluation (B6)

- [ ] **Honest normalization ablation.** `search(normalize=False)` only skips normalization on the query side, while the index stays transliterated. B6 needs a real "no normalization" index variant: a second `search_vector` over the raw text, or a separate index build. Otherwise the RQ3 normalization result is overstated.
