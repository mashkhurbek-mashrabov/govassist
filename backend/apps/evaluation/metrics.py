"""Evaluation metrics (plan §7). Pure functions: no database, no network.

Every per-question score is a number, a bool or None ("does not apply"); aggregates ignore
None, so a metric is averaged only over the questions it applies to.
"""

import statistics
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from django.conf import settings

from apps.common.text import detect_script
from apps.evaluation.constants import (
    GROUP_FIELDS,
    JUDGE_METRICS,
    PERCENTILES,
    RATE_METRICS,
    RECALL_K,
    SCRIPT,
    TOKENS_PER_PRICE_UNIT,
    Category,
)
from apps.evaluation.models import EvalQuestion

type Score = float | bool | None


def recall_at_k(
    expected: Sequence[str], retrieved: Sequence[str], k: int = RECALL_K
) -> float | None:
    """Share of the expected documents found in the top ``k`` retrieved documents.

    Args:
        expected: Expected document ids.
        retrieved: Retrieved document ids, best first (one per document).
        k: Cut-off.
    """
    if not expected:
        return None
    return len(set(expected) & set(retrieved[:k])) / len(set(expected))


def reciprocal_rank(expected: Sequence[str], retrieved: Sequence[str]) -> float | None:
    """1 / rank of the first expected document in the retrieved list (0 when absent).

    Args:
        expected: Expected document ids.
        retrieved: Retrieved document ids, best first.
    """
    if not expected:
        return None
    wanted = set(expected)
    return next((1 / rank for rank, doc in enumerate(retrieved, start=1) if doc in wanted), 0.0)


def citation_validity(cited_labels: Sequence[str], known_labels: Iterable[str]) -> float | None:
    """Share of the model's source ids that point to a retrieved block (None if it cites none).

    Args:
        cited_labels: Every ``source_ids`` entry the model wrote (before cleaning).
        known_labels: The labels it was given (``S1..Sn``).
    """
    if not cited_labels:
        return None
    known = set(known_labels)
    return sum(label in known for label in cited_labels) / len(cited_labels)


def office_routing(question: EvalQuestion, office: Mapping[str, Any] | None) -> bool | None:
    """True when the office card has the expected type in the asker's district.

    Args:
        question: The question (``expected_office_type`` and ``district``).
        office: The ``OfficeMatch`` shown with the answer, if any.
    """
    if not question.expected_office_type or question.district_id is None:
        return None
    if not office or office.get("match") != "district":
        return False
    shown = office.get("office") or {}
    return (
        office["office_type"]["code"] == question.expected_office_type
        and (shown.get("district") or {}).get("id") == question.district_id
    )


def refusal_correct(question: EvalQuestion, refused: bool) -> bool:
    """A refusal is right exactly when the question is out of scope or not in the corpus.

    Args:
        question: The question.
        refused: Whether the answer refused (not_found / off_topic).
    """
    should_refuse = question.category == Category.OUT_OF_SCOPE or not question.in_corpus
    return refused == should_refuse


def script_consistent(question: EvalQuestion, answer_text: str) -> bool | None:
    """The answer is written in the question's script (None for an empty answer).

    Args:
        question: The question (``script``).
        answer_text: The answer's visible text.
    """
    if not answer_text.strip():
        return None
    return detect_script(answer_text) == question.script


def text_scores(question: EvalQuestion, answer_text: str) -> dict[str, Score]:
    """The scores that apply to a plain-text answer (external chatbots).

    Args:
        question: The question.
        answer_text: The transcribed answer.
    """
    return {SCRIPT: script_consistent(question, answer_text)}


def cost_usd(prompt_tokens: int, completion_tokens: int) -> float | None:
    """Generation cost from the configured prices (None when prices are not set).

    Args:
        prompt_tokens: Input tokens.
        completion_tokens: Output (incl. thinking) tokens.
    """
    price_in = float(settings.EVAL_PRICE_INPUT_PER_M)
    price_out = float(settings.EVAL_PRICE_OUTPUT_PER_M)
    if not price_in and not price_out:
        return None
    return (prompt_tokens * price_in + completion_tokens * price_out) / TOKENS_PER_PRICE_UNIT


def _mean(values: Iterable[Score]) -> float | None:
    """Mean of the applicable values (bools count as 0/1)."""
    numbers = [float(value) for value in values if value is not None]
    return statistics.fmean(numbers) if numbers else None


def percentile(values: Sequence[float], q: int) -> float | None:
    """The ``q``-th percentile (inclusive method), None for no values.

    Args:
        values: Samples.
        q: 1..99.
    """
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])
    return statistics.quantiles(values, n=100, method="inclusive")[q - 1]


def aggregate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Run-level numbers from per-question rows (``scores``, latency, tokens, cost).

    Args:
        rows: One mapping per question with ``scores``, ``latency_ms``, ``prompt_tokens``,
            ``completion_tokens`` and ``cost_usd``.

    Returns:
        Means per metric (with the number of questions each applies to), latency
        percentiles, token and cost totals.
    """
    result: dict[str, Any] = {"questions": len(rows)}
    for key in (*RATE_METRICS, *JUDGE_METRICS):
        values = [row["scores"].get(key) for row in rows]
        result[key] = _mean(values)
        result[f"{key}_n"] = sum(value is not None for value in values)
    latencies = [row["latency_ms"] for row in rows if row.get("latency_ms") is not None]
    for q in PERCENTILES:
        result[f"latency_p{q}_ms"] = percentile(latencies, q)
    result["prompt_tokens"] = sum(row.get("prompt_tokens") or 0 for row in rows)
    result["completion_tokens"] = sum(row.get("completion_tokens") or 0 for row in rows)
    costs = [row["cost_usd"] for row in rows if row.get("cost_usd") is not None]
    result["cost_usd"] = sum(costs) if costs else None
    result["cost_per_answer_usd"] = result["cost_usd"] / len(costs) if costs else None
    return result


def by_group(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    """``aggregate`` per language, per script and per category.

    Args:
        rows: Per-question rows, each with the ``GROUP_FIELDS`` keys.
    """
    groups: dict[str, dict[str, list[Mapping[str, Any]]]] = {
        f: defaultdict(list) for f in GROUP_FIELDS
    }
    for row in rows:
        for field in GROUP_FIELDS:
            groups[field][row[field]].append(row)
    return {
        field: {value: aggregate(members) for value, members in sorted(values.items())}
        for field, values in groups.items()
    }


def cohen_kappa(a: Sequence[int], b: Sequence[int]) -> float | None:
    """Cohen's κ between two raters' labels on the same items (None when undefined).

    Args:
        a: First rater's labels.
        b: Second rater's labels (same order and length).

    Raises:
        ValueError: When the lengths differ.
    """
    if len(a) != len(b):
        msg = "raters must label the same items"
        raise ValueError(msg)
    if not a:
        return None
    n = len(a)
    labels = set(a) | set(b)
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / n
    expected = sum((a.count(label) / n) * (b.count(label) / n) for label in labels)
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)
