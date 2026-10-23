"""Run a question set through the GovAssist answer path, non-streaming (plan §7).

The same building blocks as ``AnswerService`` (search, build_context, locate, render_prompt,
the generator, Answer validation, resolve_citations), with the ablation switches applied and
without conversations, quotas or streaming. Collaborators are injected so tests use fakes.
"""

import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from asgiref.sync import sync_to_async
from django.conf import settings
from django.utils import timezone
from pydantic import ValidationError

from apps.chat.citations import resolve_citations
from apps.chat.generator import AnswerGenerator
from apps.chat.prompts import render_prompt
from apps.chat.schemas import Answer, Item, LawPoint
from apps.chat.service import build_context
from apps.common.constants import MS_PER_S, Lang
from apps.corpus.embeddings import Embedder
from apps.evaluation import metrics
from apps.evaluation.constants import (
    CITATION_VALIDITY,
    JUDGE_CORRECTNESS,
    JUDGE_GROUNDED,
    JUDGE_UNSUPPORTED,
    MRR,
    OFFICE_ROUTING,
    RECALL,
    REFUSAL,
    SCRIPT,
    VALID_JSON,
    RunKind,
)
from apps.evaluation.judge import Judge
from apps.evaluation.models import EvalQuestion, EvalResult, EvalRun
from apps.offices.locator import locate
from apps.offices.selectors import aoffice_type_label
from apps.retrieval.search import Hit, Mode, search


@dataclass(frozen=True)
class EvalConfig:
    """The ablation switches of one run (stored on ``EvalRun.config``)."""

    mode: Mode
    normalize: bool
    rag: bool
    prompt_version: str


@dataclass(frozen=True)
class Pipeline:
    """Collaborators of a run: Gemini in production, fakes in tests."""

    embedder: Embedder
    generator_factory: Callable[[], AnswerGenerator]
    judge: Judge | None = None
    searcher: Callable[..., list[Hit]] = search
    locator: Callable[..., dict[str, Any] | None] = locate


def _answer_text(answer: Answer) -> str:
    """The visible text of an answer, as one string (script check, judge input)."""
    parts = [answer.title, answer.summary]
    parts += [item.text for item in (*answer.steps, *answer.documents)]
    parts += [item.text for item in (answer.fee, answer.processing_time) if item is not None]
    parts += [f"{point.quote} — {point.explanation}" for point in answer.law_points]
    return "\n".join(part for part in parts if part)


def _cited_labels(answer: Answer) -> list[str]:
    """Every ``source_ids`` entry the model wrote, before citation cleaning."""
    items: list[Item | LawPoint] = [*answer.steps, *answer.documents, *answer.law_points]
    items += [item for item in (answer.fee, answer.processing_time) if item is not None]
    return [label for item in items for label in item.source_ids]


async def _retrieve(question: EvalQuestion, config: EvalConfig, pipeline: Pipeline) -> list[Hit]:
    """Hits for the question under the run's mode and normalization (none without RAG)."""
    if not config.rag:
        return []
    vector = None
    if config.mode != "keyword":
        vector = await pipeline.embedder.embed_query(question.question)
    return await sync_to_async(pipeline.searcher)(
        question.question,
        question.language,
        query_vector=vector,
        mode=config.mode,
        normalize=config.normalize,
    )


async def answer_question(
    run: EvalRun, question: EvalQuestion, config: EvalConfig, pipeline: Pipeline
) -> EvalResult:
    """Answer one question, score it and store the result.

    Args:
        run: The run.
        question: The question.
        config: The ablation switches.
        pipeline: The collaborators.

    Returns:
        The stored result (``error`` set when the answer was not valid JSON).
    """
    started = time.perf_counter()
    hits = await _retrieve(question, config, pipeline)
    context = await sync_to_async(build_context)(hits)
    doc_ids = [str(doc) for doc in dict.fromkeys(hit.document_id for hit in context.hits)]
    district = await sync_to_async(lambda: question.district)()
    office = None
    if doc_ids:
        office = await sync_to_async(pipeline.locator)(
            list(dict.fromkeys(hit.document_id for hit in context.hits)),
            district_id=question.district_id,
            region_id=district.region_id if district else None,
            lang=question.language,
        )
    prompt = render_prompt(
        version=config.prompt_version,
        language=Lang(question.language),
        question=question.question,
        context=context.blocks,
        history=[],
        office_type_label=await aoffice_type_label(office, question.language),
    )
    generator = pipeline.generator_factory()
    raw = "".join([fragment async for fragment in generator.stream(prompt)])
    latency_ms = int((time.perf_counter() - started) * MS_PER_S)
    usage = generator.usage
    common = {
        "run": run,
        "question": question,
        "retrieved_doc_ids": doc_ids,
        "latency_ms": latency_ms,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
    }
    try:
        parsed = Answer.model_validate_json(raw)
    except ValidationError:
        invalid = {
            VALID_JSON: False,
            RECALL: metrics.recall_at_k(question.expected_doc_ids, doc_ids) if config.rag else None,
        }
        return await EvalResult.objects.acreate(error="invalid_answer", scores=invalid, **common)
    citations = resolve_citations(parsed, context.sources)
    if parsed.bare:
        office = None  # as in chat: refusals and smalltalk show no office card
    text = _answer_text(citations.answer)
    scores: dict[str, Any] = {
        VALID_JSON: True,
        RECALL: metrics.recall_at_k(question.expected_doc_ids, doc_ids) if config.rag else None,
        MRR: metrics.reciprocal_rank(question.expected_doc_ids, doc_ids) if config.rag else None,
        CITATION_VALIDITY: metrics.citation_validity(_cited_labels(parsed), context.sources),
        OFFICE_ROUTING: metrics.office_routing(question, office) if config.rag else None,
        REFUSAL: metrics.refusal_correct(question, parsed.refused),
        SCRIPT: metrics.script_consistent(question, text),
    }
    if pipeline.judge is not None:
        sources = "\n\n".join(f"[{block.label}] {block.text}" for block in context.blocks)
        verdict = await sync_to_async(pipeline.judge.judge)(
            question=question.question,
            expected_facts=question.expected_facts,
            answer=text,
            sources=sources,
        )
        scores |= {
            JUDGE_CORRECTNESS: verdict.correctness,
            JUDGE_GROUNDED: verdict.grounded,
            JUDGE_UNSUPPORTED: verdict.unsupported_claims,
        }
    doc_of_label = {
        block.label: str(hit.document_id)
        for block, hit in zip(context.blocks, context.hits, strict=True)
    }
    cited_docs = list(
        dict.fromkeys(doc_of_label[label] for label in sorted(citations.cited_labels))
    )
    return await EvalResult.objects.acreate(
        answer=citations.answer.model_dump(by_alias=True),
        cited_doc_ids=cited_docs,
        office_match=office,
        scores=scores,
        **common,
    )


async def run_eval(
    *, name: str, version: str, config: EvalConfig, pipeline: Pipeline, git_sha: str = ""
) -> EvalRun:
    """Answer every question of ``version`` in order and store the run.

    Args:
        name: Run name (also the report file name).
        version: Question-set version.
        config: The ablation switches.
        pipeline: The collaborators.
        git_sha: Code version, when known.

    Returns:
        The finished run.

    Raises:
        ValueError: When the question set is empty.
    """
    questions: Sequence[EvalQuestion] = [
        q async for q in EvalQuestion.objects.filter(version=version)
    ]
    if not questions:
        msg = f"No questions for version {version!r}: run load_eval_questions first."
        raise ValueError(msg)
    run = await EvalRun.objects.acreate(
        name=name,
        kind=RunKind.GOVASSIST,
        question_version=version,
        config=asdict(config),
        corpus_version=settings.CORPUS_VERSION,
        prompt_version=config.prompt_version,
        git_sha=git_sha,
        model_names={
            "generator": pipeline.generator_factory().model_name,
            "embedding": settings.GEMINI_EMBEDDING_MODEL if config.rag else None,
            "judge": pipeline.judge.model if pipeline.judge else None,
        },
        started_at=timezone.now(),
    )
    for question in questions:
        await answer_question(run, question, config, pipeline)
    run.finished_at = timezone.now()
    await run.asave(update_fields=["finished_at", "updated_at"])
    return run
