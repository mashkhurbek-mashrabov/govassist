"""Unit tests for the evaluation metrics (no database)."""

from typing import Any

import pytest
from django.test import override_settings

from apps.evaluation import metrics
from apps.evaluation.constants import RECALL, REFUSAL, SCRIPT, Category, Script
from apps.evaluation.models import EvalQuestion


def question(**fields: Any) -> EvalQuestion:
    """An unsaved question with sensible defaults."""
    defaults: dict[str, Any] = {
        "qid": "NAMUNA-1",
        "version": "t",
        "question": "NAMUNA?",
        "language": "uz-Latn",
        "script": Script.LATN,
        "group_id": "g",
        "category": Category.SERVICE,
    }
    return EvalQuestion(**(defaults | fields))


def test_recall_and_mrr() -> None:
    """Recall@5 counts expected docs in the top 5; MRR uses the first hit's rank."""
    expected = ["a", "b"]
    retrieved = ["x", "a", "y", "z", "w", "b"]
    assert metrics.recall_at_k(expected, retrieved) == 0.5
    assert metrics.reciprocal_rank(expected, retrieved) == 0.5
    assert metrics.reciprocal_rank(expected, ["x"]) == 0.0


def test_retrieval_metrics_skip_questions_without_gold_docs() -> None:
    """No expected docs means the metric does not apply (None, not 0)."""
    assert metrics.recall_at_k([], ["a"]) is None
    assert metrics.reciprocal_rank([], ["a"]) is None


def test_citation_validity() -> None:
    """Share of cited labels that were in the context; None when nothing is cited."""
    assert metrics.citation_validity(["S1", "S7"], ["S1", "S2"]) == 0.5
    assert metrics.citation_validity([], ["S1"]) is None


def test_refusal_correct() -> None:
    """Out-of-scope and not-in-corpus questions must be refused; others must not."""
    out = question(category=Category.OUT_OF_SCOPE)
    missing = question(in_corpus=False)
    normal = question()
    assert metrics.refusal_correct(out, refused=True)
    assert metrics.refusal_correct(missing, refused=True)
    assert not metrics.refusal_correct(normal, refused=True)
    assert metrics.refusal_correct(normal, refused=False)


def test_script_consistent() -> None:
    """The answer must keep the question's script; empty answers do not count."""
    latin = question()
    cyrillic = question(script=Script.CYRL, language="uz-Cyrl")
    assert metrics.script_consistent(latin, "Pasport olish uchun ariza bering.")
    assert not metrics.script_consistent(latin, "Паспорт олиш учун ариза беринг.")
    assert metrics.script_consistent(cyrillic, "Паспорт олиш учун ариза беринг.")
    assert metrics.script_consistent(latin, "  ") is None


def test_office_routing() -> None:
    """Type and district must both match, and only a district-level match counts."""
    q = question(expected_office_type="migration", district_id=7)
    good = {
        "match": "district",
        "office_type": {"code": "migration"},
        "office": {"district": {"id": 7}},
    }
    assert metrics.office_routing(q, good) is True
    assert metrics.office_routing(q, good | {"match": "region"}) is False
    assert metrics.office_routing(q, good | {"office_type": {"code": "tax"}}) is False
    assert metrics.office_routing(q, None) is False
    assert metrics.office_routing(question(), good) is None


def test_cost_needs_prices() -> None:
    """Without prices cost is unknown (None), never a made-up 0."""
    with override_settings(EVAL_PRICE_INPUT_PER_M=0.0, EVAL_PRICE_OUTPUT_PER_M=0.0):
        assert metrics.cost_usd(1000, 1000) is None
    with override_settings(EVAL_PRICE_INPUT_PER_M=1.0, EVAL_PRICE_OUTPUT_PER_M=2.0):
        assert metrics.cost_usd(1_000_000, 500_000) == pytest.approx(2.0)


def test_percentile() -> None:
    """Percentiles handle 0, 1 and many samples."""
    assert metrics.percentile([], 50) is None
    assert metrics.percentile([7.0], 95) == 7.0
    assert metrics.percentile([1.0, 2.0, 3.0], 50) == 2.0


def test_aggregate_and_groups() -> None:
    """Means skip None, report how many questions each metric covers, and split by group."""
    rows = [
        {
            "language": "ru",
            "script": "cyrl",
            "category": "service",
            "latency_ms": 100,
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "cost_usd": None,
            "scores": {RECALL: 1.0, REFUSAL: True, SCRIPT: True},
        },
        {
            "language": "en",
            "script": "latn",
            "category": "legal",
            "latency_ms": 300,
            "prompt_tokens": 20,
            "completion_tokens": 5,
            "cost_usd": None,
            "scores": {RECALL: None, REFUSAL: False, SCRIPT: True},
        },
    ]
    overall = metrics.aggregate(rows)
    assert overall[RECALL] == 1.0
    assert overall[f"{RECALL}_n"] == 1
    assert overall[REFUSAL] == 0.5
    assert overall["latency_p50_ms"] == 200.0
    assert overall["prompt_tokens"] == 30
    assert overall["cost_usd"] is None
    groups = metrics.by_group(rows)
    assert set(groups["language"]) == {"ru", "en"}
    assert groups["category"]["legal"][REFUSAL] == 0.0


def test_cohen_kappa() -> None:
    """κ is 1 for full agreement, 0-ish for chance, None when undefined."""
    assert metrics.cohen_kappa([0, 1, 2, 2], [0, 1, 2, 2]) == 1.0
    assert metrics.cohen_kappa([0, 1, 0, 1], [0, 0, 1, 1]) == 0.0
    assert metrics.cohen_kappa([], []) is None
    assert metrics.cohen_kappa([2, 2], [2, 2]) is None
    with pytest.raises(ValueError, match="same items"):
        metrics.cohen_kappa([1], [1, 2])
