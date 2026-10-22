# GovAssist — Technical Implementation Plan

Companion to `govassist-thesis-plan.md`. That document says *what* and *why*; this one says *how*.
Written for AI coding agents: concrete modules, schemas, contracts, algorithms, and commands. Where a decision is marked **FIXED**, do not change it without updating both documents.

---

## 1. Environment and tooling

| Item | Version / choice |
|---|---|
| Python | 3.12 (**FIXED**) |
| Django / DRF | 5.1 / 3.15 |
| PostgreSQL | 16 with `pgvector` ≥ 0.7 (`pgvector/pgvector:pg16` image) |
| Redis | 7 |
| Celery | 5.4 |
| Embeddings | `sentence-transformers` 3.x, model `intfloat/multilingual-e5-base` (768d) — **FIXED for v1**; `BAAI/bge-m3` evaluated in Phase 6 only |
| LLM client | `openai` Python SDK pointed at a configurable `LLM_BASE_URL` |
| Package mgmt | `uv` with `pyproject.toml`; lockfile committed |
| Lint/format/type | `ruff`, `ruff format`, `mypy --ignore-missing-imports` |
| Tests | `pytest`, `pytest-django`, `factory_boy`, `pytest-asyncio` |
| Mobile | Flutter 3.2x, Dart 3; packages: `dio`, `flutter_riverpod`, `go_router`, `flutter_markdown`, `url_launcher`, `shared_preferences`, `intl`, `speech_to_text` (optional) |
| Infra | Docker Compose v2, nginx 1.27, Certbot; GitHub Actions |

### Environment variables (`backend/.env.example`)
```
DJANGO_SETTINGS_MODULE=config.settings.dev
SECRET_KEY=
DATABASE_URL=postgres://govassist:govassist@db:5432/govassist
REDIS_URL=redis://redis:6379/0
EMBEDDING_SERVICE_URL=http://embedding:8100
EMBEDDING_MODEL=intfloat/multilingual-e5-base
EMBEDDING_DIM=768
LLM_BASE_URL=https://api.openai.com/v1        # or http://ollama:11434/v1
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini                          # generator
JUDGE_LLM_MODEL=                               # different model for eval
LLM_TIMEOUT_S=40
RAG_TOP_K_VECTOR=8
RAG_TOP_K_KEYWORD=8
RAG_FINAL_K=5
RAG_RERANKER_ENABLED=false
PROMPT_VERSION=v1
CORPUS_VERSION=2026.09
RATE_LIMIT_CHAT=30/h
```

### `docker-compose.yml` services
```yaml
services:
  db:        { image: pgvector/pgvector:pg16, volumes: [pgdata:/var/lib/postgresql/data], env_file: .env }
  redis:     { image: redis:7-alpine }
  embedding: { build: ./embedding-service, ports: ["8100:8100"], volumes: [hfcache:/root/.cache/huggingface] }
  backend:   { build: ./backend, command: gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000,
               depends_on: [db, redis, embedding], env_file: .env, ports: ["8000:8000"] }
  worker:    { build: ./backend, command: celery -A config worker -l info -Q default,embed, depends_on: [db, redis, embedding], env_file: .env }
  # prod only:
  nginx:     { image: nginx:1.27, volumes: [./deploy/nginx.conf:/etc/nginx/conf.d/default.conf, certs:/etc/letsencrypt], ports: ["80:80","443:443"] }
volumes: { pgdata: {}, hfcache: {}, certs: {} }
```
Backend runs under ASGI (uvicorn worker) because the chat endpoint streams SSE.

---

## 2. Backend project structure

```
backend/
├── config/
│   ├── settings/{base,dev,prod}.py
│   ├── urls.py
│   ├── asgi.py
│   └── celery.py
├── apps/
│   ├── common/        # BaseModel(uuid pk, created_at, updated_at), exceptions, pagination, PII scrubber
│   ├── corpus/        # models, admin, ingestion/, chunking.py, normalize.py, tasks.py
│   ├── retrieval/     # search.py (vector, keyword, fusion), rerank.py, types.py
│   ├── chat/          # prompts.py, llm.py, citations.py, service.py, views.py, serializers.py
│   ├── feedback/
│   └── eval/          # fixtures/, runner.py, metrics.py, judge.py, management/commands/run_eval.py
├── scripts/
├── tests/
└── pyproject.toml
```

Settings essentials in `base.py`:
- `INSTALLED_APPS` includes `pgvector.django` (via `pgvector` package), `rest_framework`, `drf_spectacular`, `django_ratelimit`, `corsheaders`.
- `REST_FRAMEWORK`: default auth = `DeviceTokenAuthentication`; default throttle classes anonymous.
- `CELERY_TASK_ROUTES = {"apps.corpus.tasks.embed_chunks": {"queue": "embed"}}`.
- `LOGGING`: JSON formatter (`python-json-logger`), request-id middleware adds `request_id` to every record.

---

## 3. Data model (Django)

All models inherit `common.BaseModel` (`id: UUIDField(primary_key)`, `created_at`, `updated_at`).

### `corpus`
```python
class Source(BaseModel):
    name = CharField(200)                 # "lex.uz", "my.gov.uz"
    base_url = URLField()
    publisher = CharField(200)
    licence_note = TextField()            # terms of use, quoted or linked
    robots_ok = BooleanField(default=True)

class Document(BaseModel):
    class DocType(TextChoices): LAW, DECREE, REGULATION, SERVICE_PAGE, FAQ
    class Lang(TextChoices): UZ_LATN = "uz-Latn"; UZ_CYRL = "uz-Cyrl"; RU = "ru"
    source = FK(Source)
    external_id = CharField(200, db_index=True)   # e.g. lex.uz act id
    title = CharField(500)
    doc_type = CharField(choices=DocType)
    language = CharField(choices=Lang)
    canonical_url = URLField(unique=True)
    published_at = DateField(null=True)
    fetched_at = DateTimeField()
    raw_html_path = CharField(500)        # cached on disk under /data/raw/
    text = TextField()                    # cleaned plain text with heading markers
    text_hash = CharField(64, db_index=True)
    corpus_version = CharField(20)
    is_active = BooleanField(default=True)
    service_domain = CharField(50, db_index=True)  # "passport", "civil_registry", ...

class Chunk(BaseModel):
    document = FK(Document, related_name="chunks")
    order = PositiveIntegerField()
    heading_path = CharField(500)         # "Law › Chapter 2 › Article 14"
    text = TextField()                    # original script
    text_latin = TextField()              # normalised (see §5)
    token_count = PositiveIntegerField()
    embedding = VectorField(dimensions=settings.EMBEDDING_DIM, null=True)
    search_vector = SearchVectorField(null=True)   # tsvector on text_latin
    class Meta:
        unique_together = [("document", "order")]
        indexes = [
            HnswIndex(name="chunk_emb_hnsw", fields=["embedding"], m=16, ef_construction=64, opclasses=["vector_cosine_ops"]),
            GinIndex(fields=["search_vector"]),
        ]
```
A Postgres trigger (in a migration `RunSQL`) keeps `search_vector = to_tsvector('simple', text_latin)` updated.

### `chat`
```python
class Device(BaseModel):
    token_hash = CharField(64, unique=True)      # sha256 of the device token
    platform = CharField(20); app_version = CharField(20)
    preferred_lang = CharField(10, default="uz-Latn")

class Session(BaseModel):
    device = FK(Device); language = CharField(10); title = CharField(200, blank=True)

class Message(BaseModel):
    session = FK(Session, related_name="messages")
    role = CharField(choices=[("user","user"),("assistant","assistant")])
    content = TextField()
    content_normalized = TextField(blank=True)   # user turns only
    detected_script = CharField(10, blank=True)
    retrieved_chunks = M2M(Chunk, through="Retrieval")
    model = CharField(100, blank=True); prompt_version = CharField(10, blank=True)
    prompt_tokens = IntegerField(null=True); completion_tokens = IntegerField(null=True)
    latency_ms = IntegerField(null=True); retrieval_ms = IntegerField(null=True)
    refused = BooleanField(default=False)

class Retrieval(BaseModel):
    message = FK(Message); chunk = FK(Chunk)
    rank = IntegerField(); vector_score = FloatField(null=True); keyword_score = FloatField(null=True); fused_score = FloatField()
    cited = BooleanField(default=False)
```

### `feedback`
```python
class Feedback(BaseModel):
    message = OneToOne(Message); rating = SmallIntegerField(choices=[(1,"up"),(-1,"down")]); comment = TextField(blank=True)
```

### `eval`
```python
class EvalQuestion(BaseModel):
    qid = CharField(20, unique=True)      # "UZL-001"
    question = TextField(); language = CharField(10); script = CharField(10)
    group_id = CharField(20)              # links UZ-Latn / UZ-Cyrl / RU variants of the same question
    expected_facts = JSONField()          # ["docs: passport, application", "fee: 0", ...]
    expected_doc_ids = JSONField()        # list of Document.external_id
    in_corpus = BooleanField(default=True)
    version = CharField(10)

class EvalRun(BaseModel):
    name = CharField(100); config = JSONField(); corpus_version = CharField(20); prompt_version = CharField(10)
    started_at = DateTimeField(); finished_at = DateTimeField(null=True)

class EvalResult(BaseModel):
    run = FK(EvalRun); question = FK(EvalQuestion)
    answer = TextField(); retrieved_doc_ids = JSONField(); cited_doc_ids = JSONField()
    scores = JSONField()                  # {"recall@5":1,"mrr":0.5,"correctness":2,"grounded":true,"refused":false,"latency_ms":1830}
```

---

## 4. Ingestion pipeline (`apps/corpus/ingestion/`)

```
fetch → cache raw → parse → clean → Document upsert → chunk → embed
```

- `fetchers/lexuz.py`, `fetchers/mygov.py`: each exposes `iter_items(domain) -> Iterator[RawItem]` and `fetch(item) -> RawPage`. Use `httpx` with `Retry-After` handling, 1 req/s per host, `User-Agent: GovAssist-research/1.0 (+contact email)`. Check `robots.txt` with `urllib.robotparser`; skip disallowed URLs and log them.
- Cache raw HTML/PDF to `/data/raw/<source>/<external_id>.<ext>`; never re-fetch if hash unchanged.
- `parsers/html.py`: `selectolax` → drop nav/footer/scripts → keep headings (`h1–h4`) as markers `\n## <text>\n`, paragraphs, lists, tables (flatten rows as `cell | cell`).
- `parsers/pdf.py`: `pdfplumber` text with layout; detect headings by font size/regex (`^Модда \d+`, `^\d+-modda`).
- `clean.py`: normalise whitespace, unify quotes, remove page headers/footers repeated on every page, keep article numbering.
- `Document` upsert keyed on `canonical_url`; if `text_hash` changed → mark old chunks inactive, rechunk, re-embed.
- Management commands: `ingest --source lexuz --domain passport --limit 50`, `rechunk --doc <id>`, `rebuild_index`.

---

## 5. Chunking and Uzbek normalisation

### Chunking (`chunking.py`) — **FIXED for v1**
1. Split on heading markers to get sections with a `heading_path`.
2. Within a section, split into paragraphs; pack paragraphs greedily into chunks of ≤ 500 tokens (tokeniser: `tiktoken` `cl100k_base` as a proxy), with 80-token overlap taken from the tail of the previous chunk.
3. Prefix each chunk's embedding input with `heading_path + "\n"`. E5 requires `"passage: "` prefix for documents and `"query: "` for queries — apply in the embedding client, not in stored text.
4. Store `token_count`; reject chunks < 30 tokens unless they are the only chunk in a section.

### Normalisation (`normalize.py`)
```python
CYR2LAT = {"а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"yo","ж":"j","з":"z","и":"i","й":"y","к":"k","л":"l",
           "м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"x","ц":"ts","ч":"ch","ш":"sh",
           "ъ":"ʼ","ь":"","э":"e","ю":"yu","я":"ya","ў":"oʻ","қ":"q","ғ":"gʻ","ҳ":"h"}
APOSTROPHES = {"ʻ","ʼ","'","`","‘","’","ʹ"}   # collapse to "ʻ" after o/g (modifier), "ʼ" elsewhere
```
- `detect_script(text) -> "uz-Latn" | "uz-Cyrl" | "ru"`: ratio of Cyrillic letters; distinguish Uzbek Cyrillic from Russian by presence of `ў қ ғ ҳ` or Uzbek stop-words (`ва`, `учун`, `билан`) vs Russian stop-words (`и`, `для`, `с`). Fallback `langdetect`.
- `to_latin(text)`: apply `CYR2LAT` char-wise with context rules (`е` at word start / after vowel → `ye`; `ц` → `s` at word start in loanwords is out of scope).
- `canonicalize(text)`: lowercase, unify apostrophes, collapse whitespace, strip punctuation for keyword search.
- Russian text is **not** transliterated; `text_latin = canonicalize(text)` for Russian docs.
- Golden test file `tests/fixtures/translit_golden.tsv` with 50 word pairs; test must pass 50/50.

---

## 6. Embedding service (`embedding-service/`)

Minimal HTTP server (standard-library `http.server` or `uvicorn` + a 40-line ASGI app — no framework needed):
- `POST /embed` `{"texts": [...], "kind": "query"|"passage"}` → `{"vectors": [[...]], "model": "...", "dim": 768}`.
- Prefixes `query: ` / `passage: ` for E5. Batch size 64, `normalize_embeddings=True`.
- `GET /health`.
- Model cached in the `hfcache` volume; CPU is sufficient for the pilot corpus (~10k chunks ≈ minutes).

Backend client `apps/corpus/embeddings.py`: `embed_passages(list[str])`, `embed_query(str)`, with 3 retries and a circuit breaker (fail fast for 30 s after 3 consecutive failures).

Celery task `embed_chunks(chunk_ids: list[UUID])` on queue `embed`: loads chunks, calls service, bulk-updates `embedding`. `ingest` enqueues in batches of 64.

---

## 7. Retrieval (`apps/retrieval/search.py`)

```python
@dataclass
class Hit: chunk_id: UUID; document_id: UUID; vector_score: float|None; keyword_score: float|None; fused: float; rank: int

def vector_search(qvec, k) -> list[Hit]:
    # Chunk.objects.filter(document__is_active=True).annotate(d=CosineDistance("embedding", qvec)).order_by("d")[:k]

def keyword_search(q_latin, k) -> list[Hit]:
    # SearchQuery(q_latin, config="simple", search_type="websearch") on search_vector; rank via SearchRank

def rrf(lists: list[list[Hit]], k=60) -> list[Hit]:
    # fused = Σ 1/(k + rank_i); dedupe by chunk_id; sort desc

def search(query: str, lang: str) -> list[Hit]:
    q_norm = canonicalize(to_latin(query) if detect_script(query)=="uz-Cyrl" else query)
    v = vector_search(embed_query(q_norm), settings.RAG_TOP_K_VECTOR)
    kw = keyword_search(q_norm, settings.RAG_TOP_K_KEYWORD)
    hits = rrf([v, kw])[: settings.RAG_FINAL_K * 2]
    if settings.RAG_RERANKER_ENABLED: hits = rerank(query, hits)
    return diversify(hits, max_per_doc=2)[: settings.RAG_FINAL_K]
```
- `diversify`: at most 2 chunks per document so the context covers ≥ 3 documents when available.
- Retrieval mode is selectable per call (`mode="vector"|"keyword"|"hybrid"`) — needed for Phase 6 ablations.
- Set `SET hnsw.ef_search = 100` at connection start for better recall on small corpora.

---

## 8. Answer generation (`apps/chat/`)

### Prompt (`docs/prompts/v1.md`, loaded at startup, hashed into `Message.prompt_version`)
```
SYSTEM
You are GovAssist, an assistant that explains public services in Uzbekistan.
Rules:
1. Use ONLY the CONTEXT below. If it does not contain the answer, say you don't have this information and suggest the closest covered service. Never guess fees, deadlines, or document lists.
2. Answer in the same language and script as the QUESTION ({lang}).
3. Structure: one-sentence summary → numbered steps → "Required documents" → "Fee" → "Deadline" → "Where to apply". Omit a section only if the context lacks it and say so.
4. After every factual sentence add a citation like [doc:<id>] using the ids in CONTEXT.
5. End with: "{disclaimer}"
6. If the question is not about public services, politely decline in one sentence.

CONTEXT
[doc:{document.external_id}] {document.title} — {chunk.heading_path} ({published_at})
{chunk.text}
---
(repeat)

HISTORY (last 4 turns, may be empty)
...
QUESTION
{question}
```
Disclaimers are stored per language in `apps/chat/i18n.py`.

### LLM client (`llm.py`)
- `openai.AsyncOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)`.
- `stream_chat(messages, model, temperature=0.1, max_tokens=900, timeout=LLM_TIMEOUT_S)` yields text deltas; on completion returns usage.
- Retries: 2, exponential backoff, only on 429/5xx/timeout. No retry after first token has been sent to the client.
- Token budget: system + context ≤ 6000 tokens; drop lowest-ranked chunk until it fits.

### Citations (`citations.py`)
- Regex `\[doc:([A-Za-z0-9._-]+)\]`. Map ids → documents from the retrieval set; unknown ids are stripped and counted (`Message.scores["invalid_citations"]`).
- Output `sources`: unique documents in order of first citation, with `title`, `heading_path` of the best chunk, `url`, `published_at`.

### Service (`service.py`)
```python
async def answer(session, user_text) -> AsyncIterator[Event]:
    t0 = now()
    script = detect_script(user_text); hits = search(user_text, session.language)
    msgs = build_prompt(user_text, hits, history(session, 4), lang=session.language)
    yield Event("sources_pending")
    async for delta in stream_chat(msgs): buffer += delta; yield Event("delta", delta)
    text, sources = parse_citations(buffer, hits)
    persist(...)  # Message + Retrieval rows, latency, tokens, refused flag (heuristic: no citations and contains refusal phrase)
    yield Event("sources", sources); yield Event("done", {"message_id": ..., "latency_ms": ...})
```
- `refused` heuristic: zero valid citations **and** answer matches a per-language "don't have this information" pattern.
- PII scrubber (`common/pii.py`) runs on `content` before logging (not before storage): passport `[A-Z]{2}\d{7}`, PINFL `\d{14}`, phones `\+?998\d{9}`.
- Response cache: Redis key `sha256(prompt_version|corpus_version|lang|canonicalize(question))`, TTL 7 days, only for single-turn questions.

---

## 9. Public API (`/api/v1/`)

Auth: header `X-Device-Token: <random 32 bytes hex>` generated by the app on first launch; backend stores `sha256` and creates `Device`. No accounts.

| Method | Path | Body / notes | Response |
|---|---|---|---|
| GET | `/health` | — | `{db, redis, embedding, llm: "ok"|"fail"}` |
| POST | `/devices` | `{platform, app_version, preferred_lang}` | `201 {device_id}` |
| POST | `/sessions` | `{language}` | `201 {id, created_at}` |
| GET | `/sessions?limit=20` | — | list with `title`, `updated_at` |
| GET | `/sessions/{id}/messages` | — | messages with `sources[]` |
| POST | `/sessions/{id}/chat` | `{text}` → **SSE stream** | see below |
| POST | `/messages/{id}/feedback` | `{rating: 1|-1, comment?}` | `201` |
| GET | `/services?lang=` | — | catalogue: `[{domain, title, sample_questions[]}]` |
| GET | `/documents/{id}` | — | `{title, url, published_at, doc_type}` |
| GET | `/schema/`, `/schema/swagger-ui/` | drf-spectacular | — |

SSE event format (`Content-Type: text/event-stream`):
```
event: delta      data: {"text":"1. Ariza..."}
event: sources    data: {"sources":[{"id":"…","title":"…","url":"…","section":"…","published_at":"…"}]}
event: done       data: {"message_id":"…","latency_ms":1830,"refused":false}
event: error      data: {"code":"llm_timeout","message":"…"}
```
Rate limit: `RATE_LIMIT_CHAT` per device; return `429` with `Retry-After`.
Errors: RFC 7807 style `{type, title, status, detail}`.

---

## 10. Mobile app (Flutter)

```
mobile/lib/
├── main.dart
├── app/ (router, theme, l10n)
├── core/ (api_client.dart [dio + SSE via http stream], device_token.dart, storage.dart)
├── features/
│   ├── onboarding/   # language picker → creates device
│   ├── chat/         # chat_screen, message_bubble (markdown), sources_row (chips → url_launcher), input_bar (text + optional mic)
│   ├── catalogue/    # domains grid → sample questions → opens chat with prefilled text
│   ├── history/      # sessions list
│   └── settings/     # language, clear data, about/disclaimer
└── l10n/ app_uz.arb, app_uz_Cyrl.arb, app_ru.arb
```
- State: Riverpod; `ChatController` holds messages, streaming buffer, pending sources.
- SSE: `dio` `ResponseType.stream`, split on `\n\n`, parse `event:`/`data:` lines; render deltas incrementally.
- Accessibility: min tap target 48dp, text scale up to 1.6, semantic labels on chips, contrast ≥ 4.5:1.
- Offline: sessions and messages cached in `sqflite`; queue feedback if offline.
- Build: `flutter build apk --release --split-per-abi`; signing config from `key.properties` (not committed).

---

## 11. Evaluation tooling (`apps/eval/`)

- Fixtures: `fixtures/questions_v1.jsonl` — one object per `EvalQuestion`. Loaded by `load_eval_questions --version v1`.
- `run_eval --name hybrid-v1 --mode hybrid --normalize on --rag on --prompt v1 --judge $JUDGE_LLM_MODEL`:
  1. Creates `EvalRun` with full config, `corpus_version`, git SHA.
  2. For each question: run the same `answer()` path (non-streaming), record retrieved/cited doc ids, latency, tokens.
  3. Metrics (`metrics.py`): `recall_at_k(expected, retrieved, k=5)`, `mrr`, `refusal_correct` (for `in_corpus=False`), `citation_validity`.
  4. Judge (`judge.py`): prompt the judge model with question, expected facts, answer, and cited chunk texts; output strict JSON `{"correctness":0|1|2,"grounded":true|false,"unsupported_claims":[...]}`. Temperature 0. Judge model must differ from generator (assert at startup).
  5. Writes `docs/results/<timestamp>_<name>.json` and a Markdown summary table; never overwrites.
- `compare_runs a b` prints deltas per metric and per language/script group.
- Manual validation: `export_judge_sample --run <id> --n 30 --seed 42` → CSV for human scoring; `judge_agreement --run <id> --csv` computes Cohen's κ.
- Ablation matrix to run in Phase 6 (each row = one `run_eval` command):

| Run | RAG | Mode | Normalise | Prompt |
|---|---|---|---|---|
| baseline-norag | off | — | — | v1-norag |
| vector | on | vector | on | v1 |
| keyword | on | keyword | on | v1 |
| hybrid | on | hybrid | on | v1 |
| hybrid-nonorm | on | hybrid | off | v1 |
| hybrid-nocite | on | hybrid | on | v1-nocite |

---

## 12. Testing strategy

- Unit: normalisation (golden file), chunker (token limits, overlap, heading paths), RRF, citation parser, PII scrubber, prompt token budgeting.
- Integration (`pytest-django`, real Postgres via docker): ingest fixture HTML → chunks → fake embedding service (deterministic vectors) → search returns expected chunk.
- API: SSE endpoint with a mocked LLM streaming fixed tokens; rate limiting; device auth.
- Contract: OpenAPI schema snapshot test (`drf-spectacular` `spectacular --validate`).
- Mobile: widget tests for chat rendering and source chips; one integration test against a local backend with the mock LLM.
- CI matrix: `lint` → `test` (services: postgres, redis) → `flutter analyze && flutter test`.

---

## 13. Observability and operations

- Logging: JSON lines; fields `ts, level, request_id, device_id(hash), session_id, event, latency_ms, tokens, model`. No raw user text at INFO level (only at DEBUG in dev).
- Metrics (`django-prometheus`, optional): request latency histogram, LLM latency histogram, retrieval latency, cache hit rate, refusals counter, feedback ratio.
- Backups: nightly `pg_dump` to the VPS disk + weekly off-box copy; raw corpus is reproducible from `/data/raw`.
- Deployment: `deploy/` contains `nginx.conf` (proxy `/api/` → backend, `proxy_buffering off` for SSE, `client_max_body_size 1m`), `Makefile` targets `up`, `migrate`, `ingest`, `backup`, `deploy`.
- Secrets only via `.env` on the server; never in the repo.

---

## 14. Implementation order for agents (checklist)

1. Phase 0: compose, settings, health endpoint, CI. ✔ when `make up && curl /api/v1/health` is green.
2. `corpus` models + migrations (pgvector ext, trigger, HNSW/GIN indexes).
3. `normalize.py` + golden tests.
4. Fetchers/parsers for one source, one domain; `ingest` command; verify 20 docs.
5. Chunker + tests; embedding service + client; `embed_chunks` task; `rebuild_index`.
6. `retrieval.search` with modes; tests; latency log.
7. Prompt v1, LLM client, citations, `answer()` service; non-streaming first, then SSE view.
8. Remaining API endpoints, device auth, rate limits, OpenAPI.
9. Flutter app: onboarding → chat (streaming) → sources → catalogue → history → settings.
10. `eval` app: fixtures loader, runner, metrics, judge, compare, export/agreement.
11. Deployment scripts, nginx, TLS, backups; production smoke test.
12. Run the ablation matrix; freeze corpus and prompt versions; hand results to the thesis.

Stop and ask the author before: changing `EMBEDDING_MODEL`, chunk size/overlap, prompt structure, or adding any external service — each invalidates evaluation results.
