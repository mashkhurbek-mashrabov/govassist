# GovAssist: Main Plan

**Thesis title:** *Development of an Intelligent Assistant for Navigating Government and Public Services Based on Retrieval-Augmented Generation Technology*
**Programme:** MSc in Program Engineering, ITPU (EPAM).
**Author:** Mashkhurbek Mashrabov.
**Plan date:** 2026-10-22. It replaces the mobile-app plans in `docs/archive/`.

Related documents:

| Doc | Purpose |
|---|---|
| [`docs/contract.md`](../contract.md) | API, SSE stream and answer schema shared by backend and frontend (**source of truth**) |
| [`01-design-plan.md`](01-design-plan.md) | Design system and screens, with the design-session prompt |
| [`02-backend-plan.md`](02-backend-plan.md) | Django backend, RAG, crawler and admin, with the backend-session prompt |
| [`03-frontend-plan.md`](03-frontend-plan.md) | React SPA, with the frontend-session prompt |
| [`/AGENTS.md`](../../AGENTS.md) | Rules for every AI agent and human contributor |

---

## 1. Problem and goal

People in Uzbekistan still queue at government offices, and they often go to the **wrong office** because information is scattered across legal texts (lex.uz), service portals (my.gov.uz) and outdated pages. This wastes their time.

**GovAssist** is a web app. A signed-in citizen asks a question in plain language (Uzbek Latin, Uzbek Cyrillic, Russian or English), for example *"Passportimni qanday qilib yangilayman?"*. The reply is a **clean, step-by-step answer** with:

- a short summary;
- numbered steps;
- required documents, fee and processing time;
- **the exact office in the user's district**: address, working hours, phone and a Google Maps link;
- sources: links to the lex.uz article or my.gov.uz page.

Legal questions are answered from lex.uz with quoted clauses and citations. Answers come **only** from a curated, reviewed knowledge base (RAG). The model is never trained, and there is no live web search.

### Non-goals

- No model training or fine-tuning.
- No voice: text-to-text only.
- No transactions: the app submits nothing to government systems.
- No legal advice: every answer carries a disclaimer and links to its sources.
- No phone/SMS sign-in.
- No live web search per question.
- No mobile app. The web app is phone-first and responsive.

---

## 2. Fixed decisions

Change these only by updating this file and `AGENTS.md`.

| Area | Decision |
|---|---|
| Product | Web app, signup **required** before the first question |
| Auth | django-allauth **headless**: Google OAuth, or email + **password** with mandatory email verification and password reset |
| Profile | Region + district (SOATO codes) are required after signup. UI language is one of `uz-Latn` (default), `uz-Cyrl`, `ru`, `en` |
| Backend | Python 3.14, **Django 6.1** (fall back to 6.0.x only if a dependency breaks), DRF, drf-spectacular, async SSE view under uvicorn (ASGI) |
| Admin | **django-unfold** |
| Frontend | React 19 + Vite + TypeScript, Tailwind CSS 4 driven by the design tokens |
| LLM | **Gemini** (paid). Generation model `gemini-3.8-flash`, embedding model `gemini-embedding-2` at 768 dims. Both IDs come from env and are recorded with every answer and eval run |
| Vector store | PostgreSQL 18 + pgvector (HNSW, cosine) + Postgres full-text search: hybrid retrieval with RRF |
| Knowledge | Two kinds:<br>(1) **text corpus**: lex.uz and my.gov.uz pages for RAG with citations;<br>(2) **office directory**: structured rows looked up by district. The LLM never writes addresses or hours |
| Data collection | Admin-curated collector: the admin adds source URLs, the system crawls, admin reviews, then the data is indexed. Office pages go through Gemini structured extraction, then review |
| Answer format | Gemini returns **JSON following a schema**, streamed over SSE. React parses the partial JSON and fills the cards live. A `final` event carries the validated answer |
| Privacy | PII (passport no., PINFL, phone, email) is scrubbed **before** anything goes to Gemini, the DB or the logs |
| Security | Same-origin, no CORS, session cookie + CSRF, verified email, per-user/IP limits, daily token caps, Cloudflare (Tunnel, Turnstile, Bot Fight, Access on admin) |
| Background jobs | `django.tasks` with the `django-tasks` database backend (`db_worker`). No Celery |
| Packages | **pip** + pip-tools (`requirements.in` compiled to hashed `requirements.txt`). No uv. npm for the frontend |
| Containers | Docker + Compose, multi-stage builds, small non-root images |
| Task runner | **invoke** (`tasks.py` at the repo root). No Makefile |
| Repo | One public monorepo: `github.com/mashkhurbek-mashrabov/govassist` |
| Code quality | Clean code, DRY, SOLID, **a docstring on every function and class**, enforced by linters (see `AGENTS.md`) |

---

## 3. Architecture

```
Browser (React SPA)
   │  HTTPS, same origin
   ▼
Cloudflare (proxy, Turnstile, Bot Fight, Access on /admin)
   │  Tunnel (cloudflared, server has no open ports)
   ▼
web: nginx-unprivileged ── serves SPA ── proxies /api, /_allauth, /static, /<admin> ──▶ backend
                                                                                         │
backend: Django 6.1 ASGI (uvicorn)                                                       │
  accounts · geo · offices · corpus · retrieval · chat · collector · evaluation         │
   │            │                 │                     │                                │
   ▼            ▼                 ▼                     ▼                                │
PostgreSQL 18  Redis 8         Gemini API           worker (crawler image, Chromium)     │
+ pgvector     (cache, limits, (generate, embed,    django.tasks db_worker:              │
               stream locks)    extract)             crawl → parse → extract → review    │
```

### Answer flow for `POST /api/v1/chat`

1. Check auth, verified email and a complete profile. Check quotas: per-user hour/day limits, one active stream, global daily token cap.
2. Scrub PII from the question. Store the user message (scrubbed text only).
3. Detect the script and language, and normalize the text (Uzbek Cyrillic to Latin for keyword search).
4. Hybrid retrieval: Gemini query embedding feeds the pgvector top-k, alongside Postgres full-text top-k. Fuse with RRF and diversify, giving the top 5 chunks.
5. If a retrieved service page maps to an office type, look up the office in the user's district (falling back to the region) and emit the `office` event early.
6. Build the prompt: system rules (versioned), context blocks `S1..Sn`, the office name/type, and the last 4 turns.
7. Stream Gemini JSON (`response_schema` = the Answer schema) as `delta` events.
8. Validate with Pydantic and strip citations to unknown sources. Persist the message, the retrieval rows, tokens and latency. Emit `final`, then `done`.

---

## 4. Repository layout

```
govassist/
├── AGENTS.md  CLAUDE.md  GEMINI.md      # agent rules (CLAUDE/GEMINI import AGENTS)
├── .claude/settings.json                # Claude Code project permissions
├── backend/                             # Django (owned by backend lane)
│   ├── AGENTS.md  CLAUDE.md
│   ├── config/settings/{base,dev,prod,test}.py
│   ├── apps/{common,accounts,geo,offices,corpus,collector,retrieval,chat,evaluation}/
│   ├── requirements{,-dev,-crawler}.{in,txt}
│   ├── pyproject.toml                   # ruff, mypy, pytest config only
│   └── Dockerfile                       # targets: runtime, crawler
├── frontend/                            # React (owned by frontend lane)
│   ├── AGENTS.md  CLAUDE.md
│   ├── src/  nginx/default.conf  Dockerfile
├── docs/
│   ├── contract.md                      # API + SSE + answer schema
│   ├── schema/                          # generated: openapi.json, answer.schema.json
│   ├── design/                          # design lane deliverables
│   ├── plans/                           # this folder
│   ├── corpus-sources.md                # every source: URL, terms, fetch date
│   ├── results/                         # eval outputs, written only by scripts
│   └── archive/
├── deploy/  (cloudflared/, backup.sh)
├── data/                                # gitignored raw crawl cache
├── compose.yaml  compose.override.yaml  compose.prod.yaml
├── tasks.py                             # invoke
└── .github/workflows/{backend,frontend}.yml
```

---

## 5. Work lanes and gates

| Lane | Agent | Branch / worktree | Owns |
|---|---|---|---|
| Coordination, review, integration | **Main session** (Claude) | `main` | `docs/contract.md`, `docs/plans/`, root agent files, design approval, merges, `web` service in compose |
| Design | **Sevara** (Claude) | `design/system-v1` | `docs/design/` |
| Backend | **Jasur** (Claude) | `feat/backend-mvp` | `backend/`, compose files, `tasks.py`, `.env.example`, `.github/workflows/backend.yml`, `deploy/`, `docs/schema/`, `docs/corpus-sources.md` |
| Frontend | **Madina** (Claude) | `feat/frontend-mvp` | `frontend/`, `.github/workflows/frontend.yml` |

Each lane works in its **own git worktree**, touches only the files it owns, and opens a PR to `main`. Contract changes go through the main session only.

**Gates:**

- **G1, contract approved.** `docs/contract.md` is merged to `main` before any lane starts.
- **G2, design approved.** The main session reviews Sevara's PR against the checklist in `01-design-plan.md` §8, then merges it and sets `docs/design/README.md` to *Status: Approved*. Madina applies visuals only after G2.
- **G3, backend MVP.** Jasur's PR passes `invoke check` and the contract tests. Madina then switches from MSW mocks to the real API.
- **G4, integration.** The main session adds the `web` service and runs the demo flow: `invoke up` → signup → verify email → onboarding → ask the passport question → streamed card + office card + sources → feedback.

---

## 6. Timeline

**Today (2026-10-22): working MVP on sample data.** Design, backend and frontend run in parallel, then integration (G4).

| Weeks (from Oct 26) | Work | Output |
|---|---|---|
| 1 | 20-question manual pilot: ChatGPT and Gemini apps, naive vs expert prompt. Finalize the source list. User supplies office source links | `docs/results/pilot/`, `docs/corpus-sources.md` |
| 2–4 | Real crawl of about 10 services and 5 codes. Offices for Tashkent city + 1 region. Admin review | Reviewed corpus v2026.11 |
| 5–6 | Retrieval tuning, prompt v1 candidate. Staging deploy behind Cloudflare | Staging URL |
| 7–9 | Eval set: 150 questions (50 uz-Latn, 50 uz-Cyrl, 50 ru) plus 30 en, from real people. Gold answers. Eval tooling | `questions_v1.jsonl` |
| 10–11 | Benchmark, baselines and ablations. Freeze corpus + prompt versions | `docs/results/*` |
| 12–13 | Usability test (3–5 people), fixes. User study (10–12 people) | SUS, task data |
| 14–20 | Thesis writing, slides, buffer | Draft by mid-March 2027 |

If ITPU's official deadline is earlier, cut scope (fewer services or regions), **never** the evaluation.

---

## 7. Research design (thesis core)

### Research questions

- **RQ1.** Does RAG with structured office data improve answer correctness and groundedness compared with the same LLM (Gemini) without retrieval?
- **RQ2.** How does GovAssist compare with general assistants (ChatGPT, Gemini app, Claude), used with naive and with expert prompts, especially on **office routing** and **citation validity**?
- **RQ3.** What is the effect of retrieval design: vector vs keyword vs hybrid, with and without Uzbek script normalization, and cross-lingual (English) queries?
- **RQ4.** Do non-technical users complete public-service information tasks more successfully and faster than with a general chatbot? How do they rate it (SUS, trust)?

### Systems compared

- A. GovAssist.
- B. Gemini without retrieval (same prompt minus context).
- C. ChatGPT, Gemini app and Claude with a naive prompt.
- D. The same three with an expert prompt ("I live in X district… use only lex.uz/my.gov.uz… cite… say if unsure").

Record the date and model version of every run.

### Question categories

- service procedure;
- office routing (region given);
- legal, factual only (fines, durations, rights stated in law);
- recently changed laws;
- out of scope or false premise.

### Metrics

- field-level fact correctness (steps, documents, fee, time);
- hallucination rate;
- citation validity;
- **office routing accuracy** (type + district);
- refusal accuracy;
- script consistency;
- Recall@5 and MRR;
- p50/p95 latency;
- cost per answer.

### Grading

- **Blind human grading** by 2–3 raters (answers shuffled, systems anonymized), reporting Cohen's/Fleiss' κ.
- An LLM judge from a **different vendor** than the generator, validated against the human scores on a 30-question sample.
- Statistics: McNemar (binary), Wilcoxon (scores), bootstrap 95% CIs.

### Gold answers without a lawyer

- Legal gold answers are **extractive**: lex.uz article ID + key clause.
- Questions stay factual.
- Optionally, one law student reviews 20 questions.
- The limitation is stated in the thesis.

### Integrity

- Results come only from scripted runs written to `docs/results/`.
- Never fabricate data, scores or participant results.

---

## 8. Thesis structure (EPAM template)

Template: Word, Times New Roman 14 pt, APA 7 citations.

| Template part | Content |
|---|---|
| Abstract + 5–7 keywords | retrieval-augmented generation; large language models; e-government; public services; Uzbek language; hybrid retrieval; conversational assistant |
| Introduction | Problem (wrong office, lost time), relevance, aim, objectives, RQs, object/subject, methods, novelty, practical value |
| Chapter 1: Literature review and problem analysis | Uzbekistan's public-service information landscape, LLM hallucination, RAG (dense/sparse/hybrid, RRF), low-resource and two-script Uzbek, e-gov chatbots, RAG evaluation, research gap |
| Chapter 2: Design and implementation | Requirements, architecture, collector (documents + offices), chunking, normalization, embeddings, hybrid retrieval, office lookup, streamed structured answers + citation checks, security, web app, deployment |
| Chapter 3: Evaluation | Benchmark design, baselines, metrics, results, ablations, office routing, user study, discussion, threats to validity |
| Conclusions | A numbered answer to each RQ, then future work |
| Annexes | **A: Uzbek abstract (mandatory)**, B: sample eval questions, C: prompts + answer schema, D: consent form + SUS, E: data model + API |

Eval scripts export tables as CSV and figures as 300-dpi PNG for pasting into Word.

---

## 9. Definition of done (thesis-ready)

- [ ] `invoke up` gives a working system on a clean machine.
- [ ] Public staging URL behind Cloudflare. A first-time user signs up and gets a correct office card within 2 minutes, unaided.
- [ ] Reviewed corpus with every source in `docs/corpus-sources.md`.
- [ ] Office directory for at least Tashkent city + 1 region, each row with a source URL and date.
- [ ] Versioned eval set (180 questions) with gold answers.
- [ ] Reproducible results for RQ1–RQ3 in `docs/results/`.
- [ ] User study with ≥ 10 participants, consent forms, SUS.
- [ ] Thesis draft with every table generated from `docs/results/`. Demo script + slides.

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| No clean office dataset | The user supplies links. Crawler + Gemini extraction + admin review. Show "data as of" on every card |
| Uzbek retrieval quality | Hybrid search + script normalization. Measure and report honestly |
| Hallucinated fees or hours | Schema-bound answers, office data from the DB only, citation stripping, groundedness metric |
| Scraping restrictions | robots.txt, 1 req/s per host, record terms of use, keep the corpus small and public |
| Personal-data localization law | Scrubbed storage. Cloudflare transit and hosting abroad listed as limitations |
| Cost or abuse | Quotas, token caps, Cloudflare, Gemini budget alerts |
| Dependency lag on Django 6.1 | Pin 6.0.x if a dependency breaks; CI catches it |
| Scope creep | Non-goals are binding. The thesis is graded on RAG + evaluation |
