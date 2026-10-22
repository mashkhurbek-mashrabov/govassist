# AGENTS.md: backend (Django)

Extends `/AGENTS.md`. Full plan: `docs/plans/02-backend-plan.md`.

## Stack

| Concern | Choice |
|---|---|
| Language / framework | Python 3.14, Django 6.1, DRF, drf-spectacular |
| Auth / admin | django-allauth (headless), django-unfold |
| Data | PostgreSQL 18 + pgvector, Redis 8 |
| Jobs | `django.tasks` + django-tasks DB backend |
| LLM | Gemini via `google-genai` |
| Packages | pip + pip-tools: edit `requirements/{base,crawler,dev}.in`, then run `invoke compile-deps`, which writes `requirements/{base,crawler,dev}.txt`. Never hand-edit the `.txt` files, never use uv |

## Structure per app

| File | Holds |
|---|---|
| `models.py`, or a **`models/` package** when the app has 2+ models | Models + invariants only. Package layout: one model per module (`models/document.py`, `models/chunk.py`), with `models/__init__.py` re-exporting them |
| `constants.py` | **All** constants of the app: limits, sizes, choices, regexes, magic strings, default values. No constant values defined anywhere else in the app. Tunables that vary per environment stay in settings/env |
| `services.py` | Business logic / writes |
| `selectors.py` | Reusable read queries |
| `api/` | Serializers, views, urls. **Thin views:** validate → service/selector → serialize. When the app has 2+ views, use **`api/views/` (and `api/serializers/`) packages**, one module per resource, like `models/` |
| `admin.py` | Unfold admin |
| `tasks.py` | Background jobs |
| `tests/` | Tests |

- No business logic in views, serializers, signals or templates.
- All models inherit `apps.common.models.BaseModel` (UUIDv7 PK, timestamps). The exception is the geo models, keyed by SOATO int.
- Every admin inherits `apps.common.admin.BaseAdmin` (subclass of `unfold.admin.ModelAdmin`). Never use plain `admin.ModelAdmin`.

## Rules

- **Docstrings:** Google style on every function, method, class and test. ruff `D` rules enforce it.
- **Types:** full annotations, `mypy --strict` clean (django-stubs, drf-stubs).
- **Settings:** every tunable lives in env, read in `config/settings/base.py` via django-environ. No hard-coded URLs, keys or limits in apps.
- **Gemini:** call it only through:
  - `apps/common/gemini.py` (the client factory);
  - `apps/corpus/embeddings.py` (`Embedder`);
  - `apps/chat/generator.py` (`AnswerGenerator`);
  - the collector extraction service.

  Never call `google.genai` elsewhere.
- **Async:**
  - The chat stream view is `async def`. Inside the async path there's no blocking I/O: use the async ORM, the async Gemini client, and `sync_to_async` for sync helpers such as retrieval.
  - Release the stream lock in `finally`.
- **Migrations:**
  - one migration per logical change;
  - never edit an applied migration;
  - add a `RunSQL` for the pgvector extension and indexes where Django can't express them.
- **API:**
  - Every endpoint has `@extend_schema`.
  - Errors are problem+json via `apps.common.problems`.
  - Responses match `docs/contract.md`, and `invoke schema` regenerates `docs/schema/`.
- **Security:**
  - Scrub PII before persistence, LLM calls and logging.
  - No raw user text in logs above DEBUG.
  - Validate all input.
  - Never mark model or crawled content safe in templates.
- **Tests:**
  - pytest + pytest-django + factory-boy.
  - Use `FakeEmbedder` / `FakeAnswerGenerator`, and saved HTML/PDF fixtures. No network.
  - Async tests use pytest-asyncio.
- **Dev server:** `uvicorn --reload` (ASGI). Don't use `runserver`: it buffers SSE.

## Commands

| Action | Command |
|---|---|
| Lint + types + tests | `invoke check` |
| Format code | `invoke format` |
| Create migrations | `invoke makemigrations` |
| Regenerate the contract schemas | `invoke schema` |
| Recompile pinned requirements | `invoke compile-deps` |
