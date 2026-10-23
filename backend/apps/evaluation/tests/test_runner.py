"""Tests for the evaluation runner and the raw-text keyword index, with fakes (no network)."""

from collections.abc import Callable
from typing import Any

import pytest
from asgiref.sync import sync_to_async

from apps.chat.generator import FakeAnswerGenerator
from apps.corpus.embeddings import FakeEmbedder
from apps.corpus.models import Document
from apps.evaluation.constants import (
    CITATION_VALIDITY,
    JUDGE_CORRECTNESS,
    MRR,
    NORAG_PROMPT,
    OFFICE_ROUTING,
    RECALL,
    REFUSAL,
    SCRIPT,
    VALID_JSON,
    Category,
)
from apps.evaluation.judge import FakeJudge
from apps.evaluation.models import EvalQuestion, EvalResult, EvalRun
from apps.evaluation.runner import EvalConfig, Pipeline, run_eval
from apps.geo.models import District
from apps.offices.models import OfficeType
from apps.retrieval.search import search
from conftest import answer_json, make_office

pytestmark = pytest.mark.django_db(transaction=True)

QUESTION = "Pasportni almashtirish uchun nima qilish kerak?"
HYBRID = EvalConfig(mode="hybrid", normalize=True, rag=True, prompt_version="v3")


def pipeline_with(
    reply: str, generators: list[FakeAnswerGenerator], judge: FakeJudge | None = None
) -> Pipeline:
    """A fake pipeline; every generator it builds is kept for prompt assertions."""

    def factory() -> FakeAnswerGenerator:
        """A new fake generator with the scripted reply."""
        generators.append(FakeAnswerGenerator(reply))
        return generators[-1]

    return Pipeline(embedder=FakeEmbedder(), generator_factory=factory, judge=judge)


@pytest.fixture
def service_question(
    passport_doc: Document, office_type: OfficeType, district: District
) -> EvalQuestion:
    """A routed service question whose gold document is the passport page."""
    make_office(office_type, district)
    return EvalQuestion.objects.create(
        qid="NAMUNA-1",
        version="t",
        question=QUESTION,
        language="uz-Latn",
        script="latn",
        group_id="g1",
        category=Category.SERVICE,
        expected_doc_ids=[str(passport_doc.id)],
        expected_office_type=office_type.code,
        district=district,
    )


async def run(config: EvalConfig, pipeline: Pipeline) -> tuple[EvalRun, EvalResult]:
    """Run version ``t`` and return the run and its single result."""
    eval_run = await run_eval(name="test-run", version="t", config=config, pipeline=pipeline)
    result = await EvalResult.objects.aget(run=eval_run)
    return eval_run, result


async def test_rag_run_scores_every_metric(
    service_question: EvalQuestion, passport_doc: Document
) -> None:
    """Hybrid RAG: the gold doc is retrieved first, the office is routed and the judge scores."""
    judge = FakeJudge()
    generators: list[FakeAnswerGenerator] = []
    eval_run, result = await run(HYBRID, pipeline_with(answer_json(), generators, judge))

    assert result.error == ""
    assert result.retrieved_doc_ids[0] == str(passport_doc.id)
    assert result.cited_doc_ids == [str(passport_doc.id)]
    assert result.scores[VALID_JSON] is True
    assert result.scores[RECALL] == 1.0
    assert result.scores[MRR] == 1.0
    assert result.scores[CITATION_VALIDITY] == 0.5  # S1 known, S7 invented
    assert result.scores[OFFICE_ROUTING] is True
    assert result.scores[REFUSAL] is True
    assert result.scores[SCRIPT] is True
    assert result.scores[JUDGE_CORRECTNESS] == 2
    assert "[S1]" in judge.calls[0]["sources"]
    assert result.prompt_tokens == 100
    assert eval_run.finished_at is not None
    assert eval_run.config == {
        "mode": "hybrid",
        "normalize": True,
        "rag": True,
        "prompt_version": "v3",
    }
    assert eval_run.model_names["judge"] == "fake-judge"


async def test_rag_off_sends_no_context(service_question: EvalQuestion) -> None:
    """``--rag off``: nothing is retrieved, the prompt has no sources, no office is shown."""
    generators: list[FakeAnswerGenerator] = []
    config = EvalConfig(mode="hybrid", normalize=True, rag=False, prompt_version=NORAG_PROMPT)
    _, result = await run(config, pipeline_with(answer_json(), generators))

    assert result.retrieved_doc_ids == []
    assert result.office_match is None
    assert "NAMUNA pasportni" not in str(generators[-1].prompts[0])
    assert result.scores[RECALL] is None
    assert result.scores[OFFICE_ROUTING] is None
    assert result.scores[CITATION_VALIDITY] == 0.0


async def test_refusal_drops_office(service_question: EvalQuestion) -> None:
    """A not_found answer to an in-corpus question is a wrong refusal and shows no office."""
    reply = answer_json(answer_type="not_found", steps=[])
    _, result = await run(HYBRID, pipeline_with(reply, []))

    assert result.office_match is None
    assert result.scores[REFUSAL] is False
    assert result.scores[OFFICE_ROUTING] is False


async def test_invalid_answer_is_recorded(service_question: EvalQuestion) -> None:
    """Invalid model JSON is stored as an error, never dropped."""
    _, result = await run(HYBRID, pipeline_with("not json", []))

    assert result.error == "invalid_answer"
    assert result.scores[VALID_JSON] is False


async def test_empty_question_set_fails() -> None:
    """A version without questions is an error, not an empty report."""
    with pytest.raises(ValueError, match="No questions"):
        await run_eval(name="x", version="none", config=HYBRID, pipeline=pipeline_with("{}", []))


@pytest.mark.parametrize(("normalize", "found"), [(True, True), (False, False)])
async def test_normalize_off_uses_raw_index(
    passport_doc: Document, normalize: bool, found: bool
) -> None:
    """A Cyrillic query finds the Latin chunk only through normalization (RQ3 ablation)."""
    hits: Callable[..., Any] = sync_to_async(search)
    result = await hits(
        "паспортни алмаштириш", "uz-Cyrl", query_vector=None, mode="keyword", normalize=normalize
    )
    assert bool(result) is found
