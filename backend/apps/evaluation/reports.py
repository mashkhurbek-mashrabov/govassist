"""Evaluation outputs under ``EVAL_RESULTS_DIR`` (docs/results): JSON, Markdown, CSV.

Files are named ``<UTC timestamp>_<name>.<ext>`` and opened in exclusive mode, so an earlier
result is never overwritten. Only scripted runs write here (AGENTS.md: research integrity).
"""

import csv
import io
import json
import random
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from django.conf import settings
from django.utils import timezone

from apps.evaluation import metrics
from apps.evaluation.constants import (
    GROUP_FIELDS,
    HUMAN_COLUMN,
    JUDGE_CORRECTNESS,
    JUDGE_METRICS,
    PERCENT,
    RATE_METRICS,
    RESULT_STAMP,
    SAFE_NAME,
    SAMPLE_COLUMNS,
)
from apps.evaluation.models import EvalResult, EvalRun


def _stem(name: str, now: datetime | None = None) -> str:
    """``<UTC timestamp>_<safe name>`` for one set of output files."""
    return f"{(now or timezone.now()).strftime(RESULT_STAMP)}_{SAFE_NAME.sub('-', name)}"


def _write(path: Path, text: str) -> Path:
    """Create ``path`` with ``text``; refuse to overwrite an existing file.

    Raises:
        FileExistsError: When the file already exists.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return path


def _rows(run: EvalRun) -> list[dict[str, Any]]:
    """Per-question rows of a run (scores plus the grouping fields)."""
    rows = []
    for result in (
        EvalResult.objects.filter(run=run).select_related("question").order_by("question__qid")
    ):
        question = result.question
        rows.append(
            {
                "result_id": str(result.id),
                "qid": question.qid,
                "language": question.language,
                "script": question.script,
                "category": question.category,
                "error": result.error,
                "latency_ms": result.latency_ms,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "cost_usd": metrics.cost_usd(
                    result.prompt_tokens or 0, result.completion_tokens or 0
                )
                if result.prompt_tokens is not None
                else None,
                "scores": result.scores,
            }
        )
    return rows


def summarize(run: EvalRun) -> dict[str, Any]:
    """The run's metadata, overall aggregates and per-group aggregates.

    Args:
        run: A finished run.
    """
    rows = _rows(run)
    return {
        "run": {
            "id": str(run.id),
            "name": run.name,
            "kind": run.kind,
            "question_version": run.question_version,
            "config": run.config,
            "corpus_version": run.corpus_version,
            "prompt_version": run.prompt_version,
            "git_sha": run.git_sha,
            "models": run.model_names,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        },
        "overall": metrics.aggregate(rows),
        "groups": metrics.by_group(rows),
        "rows": rows,
    }


def _fmt(value: Any) -> str:
    """A metric for Markdown: percentages for rates, '—' when not applicable."""
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _markdown(summary: Mapping[str, Any]) -> str:
    """A short Markdown report: config, overall table, per-group tables."""
    meta, overall = summary["run"], summary["overall"]
    lines = [
        f"# Evaluation run `{meta['name']}`",
        "",
        f"- Kind: {meta['kind']}; questions: {meta['question_version']} ({overall['questions']})",
        f"- Config: `{json.dumps(meta['config'], ensure_ascii=False)}`",
        f"- Models: `{json.dumps(meta['models'], ensure_ascii=False)}`",
        f"- Corpus {meta['corpus_version']}; prompt {meta['prompt_version']}; "
        f"git {meta['git_sha'] or 'unknown'}",
        f"- Started {meta['started_at']}, finished {meta['finished_at']}",
        "",
        "| Metric | Value | n |",
        "|---|---|---|",
    ]
    for key in (*RATE_METRICS, *JUDGE_METRICS):
        lines.append(f"| {key} | {_fmt(overall[key])} | {overall[f'{key}_n']} |")
    for key in (
        "latency_p50_ms",
        "latency_p95_ms",
        "prompt_tokens",
        "completion_tokens",
        "cost_usd",
    ):
        lines.append(f"| {key} | {_fmt(overall[key])} | |")
    for field in GROUP_FIELDS:
        lines += [
            "",
            f"## By {field}",
            "",
            "| " + field + " | n | " + " | ".join(RATE_METRICS) + " |",
        ]
        lines.append("|---|---|" + "---|" * len(RATE_METRICS))
        for value, agg in summary["groups"][field].items():
            cells = " | ".join(_fmt(agg[key]) for key in RATE_METRICS)
            lines.append(f"| {value} | {agg['questions']} | {cells} |")
    return "\n".join(lines) + "\n"


def _csv(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> str:
    """CSV text with ``columns`` (nested scores flattened by key)."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(columns), extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({**row, **row.get("scores", {})})
    return buffer.getvalue()


def write_run_report(run: EvalRun, results_dir: Path | None = None) -> list[Path]:
    """Write ``<stamp>_<name>.json``, ``.md`` and ``.csv`` for a run.

    Args:
        run: A finished run.
        results_dir: Output folder (default ``EVAL_RESULTS_DIR``).

    Returns:
        The files written.
    """
    folder = results_dir or Path(settings.EVAL_RESULTS_DIR)
    summary = summarize(run)
    stem = _stem(run.name)
    columns = (
        "qid",
        "language",
        "script",
        "category",
        "error",
        "latency_ms",
        "prompt_tokens",
        "completion_tokens",
        "cost_usd",
        *RATE_METRICS,
        *JUDGE_METRICS,
    )
    return [
        _write(folder / f"{stem}.json", json.dumps(summary, ensure_ascii=False, indent=1)),
        _write(folder / f"{stem}.md", _markdown(summary)),
        _write(folder / f"{stem}.csv", _csv(summary["rows"], columns)),
    ]


def _delta(a: Any, b: Any) -> float | None:
    """B − a for numbers, None when either is missing."""
    if isinstance(a, int | float) and isinstance(b, int | float):
        return float(b) - float(a)
    return None


def compare(a: EvalRun, b: EvalRun) -> dict[str, Any]:
    """Per-metric deltas (b − a) overall and per language / script / category.

    Args:
        a: Baseline run.
        b: Compared run.
    """
    first, second = summarize(a), summarize(b)
    keys = (*RATE_METRICS, *JUDGE_METRICS, "latency_p50_ms", "latency_p95_ms", "cost_usd")
    overall = {
        key: {
            "a": first["overall"][key],
            "b": second["overall"][key],
            "delta": _delta(first["overall"][key], second["overall"][key]),
        }
        for key in keys
    }
    groups: dict[str, dict[str, dict[str, Any]]] = {}
    for field in GROUP_FIELDS:
        shared = sorted(set(first["groups"][field]) & set(second["groups"][field]))
        groups[field] = {
            value: {
                key: _delta(first["groups"][field][value][key], second["groups"][field][value][key])
                for key in RATE_METRICS
            }
            for value in shared
        }
    return {"a": first["run"], "b": second["run"], "overall": overall, "groups": groups}


def write_comparison(a: EvalRun, b: EvalRun, results_dir: Path | None = None) -> list[Path]:
    """Write ``<stamp>_compare_<a>_vs_<b>.json`` and ``.md``.

    Args:
        a: Baseline run.
        b: Compared run.
        results_dir: Output folder (default ``EVAL_RESULTS_DIR``).
    """
    folder = results_dir or Path(settings.EVAL_RESULTS_DIR)
    result = compare(a, b)
    stem = _stem(f"compare_{a.name}_vs_{b.name}")
    lines = [
        f"# `{b.name}` vs `{a.name}` (delta = b − a)",
        "",
        "| Metric | a | b | delta |",
        "|---|---|---|---|",
    ]
    for key, values in result["overall"].items():
        lines.append(
            f"| {key} | {_fmt(values['a'])} | {_fmt(values['b'])} | {_fmt(values['delta'])} |"
        )
    for field, values in result["groups"].items():
        lines += [
            "",
            f"## Delta by {field}",
            "",
            "| " + field + " | " + " | ".join(RATE_METRICS) + " |",
        ]
        lines.append("|---|" + "---|" * len(RATE_METRICS))
        for value, deltas in values.items():
            lines.append(
                f"| {value} | " + " | ".join(_fmt(deltas[key]) for key in RATE_METRICS) + " |"
            )
    return [
        _write(folder / f"{stem}.json", json.dumps(result, ensure_ascii=False, indent=1)),
        _write(folder / f"{stem}.md", "\n".join(lines) + "\n"),
    ]


def _answer_for_humans(answer: Mapping[str, Any] | None) -> str:
    """An answer as plain text for a human grader (no system name, no scores)."""
    if not answer:
        return ""
    if "text" in answer:
        return str(answer["text"])
    parts = [answer.get("title", ""), answer.get("summary", "")]
    for field in ("steps", "documents", "law_points"):
        parts += [item.get("text") or item.get("quote", "") for item in answer.get(field) or []]
    return "\n".join(part for part in parts if part)


def write_judge_sample(run: EvalRun, n: int, seed: int, results_dir: Path | None = None) -> Path:
    """A blind CSV of ``n`` random answers for human grading (scores and system hidden).

    Args:
        run: The run to sample.
        n: Sample size (all results when smaller).
        seed: Random seed (recorded in the file name for reproducibility).
        results_dir: Output folder (default ``EVAL_RESULTS_DIR``).
    """
    results = list(EvalResult.objects.filter(run=run).select_related("question").order_by("id"))
    sample = random.Random(seed).sample(results, min(n, len(results)))  # noqa: S311 (reproducible sample, not crypto)
    rows = [
        {
            "result_id": str(result.id),
            "qid": result.question.qid,
            "language": result.question.language,
            "question": result.question.question,
            "expected_facts": "; ".join(result.question.expected_facts),
            "answer": _answer_for_humans(result.answer),
        }
        for result in sample
    ]
    folder = results_dir or Path(settings.EVAL_RESULTS_DIR)
    return _write(
        folder / f"{_stem(f'judge_sample_{run.name}_n{n}_seed{seed}')}.csv",
        _csv(rows, (*SAMPLE_COLUMNS, HUMAN_COLUMN)),
    )


def judge_agreement(
    run: EvalRun, graded_csv: Path, results_dir: Path | None = None
) -> dict[str, Any]:
    """Cohen's κ between human correctness grades and the judge on the same answers.

    Args:
        run: The judged run.
        graded_csv: The sample CSV with ``human_correctness`` filled in (0, 1 or 2).
        results_dir: Output folder (default ``EVAL_RESULTS_DIR``).

    Returns:
        The agreement figures (also written as ``<stamp>_agreement_<run>.json``).

    Raises:
        ValueError: When a graded row is not in the run, has no judge score or a bad grade.
    """
    with graded_csv.open(encoding="utf-8", newline="") as handle:
        graded = [row for row in csv.DictReader(handle) if (row.get(HUMAN_COLUMN) or "").strip()]
    judged = {
        str(r.id): r.scores.get(JUDGE_CORRECTNESS) for r in EvalResult.objects.filter(run=run)
    }
    human, judge = [], []
    for row in graded:
        score = judged.get(row["result_id"])
        if score is None:
            msg = f"result {row['result_id']} is not a judged answer of run {run.name}"
            raise ValueError(msg)
        grade = int(row[HUMAN_COLUMN])
        if grade not in (0, 1, 2):
            msg = f"human grade must be 0, 1 or 2, got {grade}"
            raise ValueError(msg)
        human.append(grade)
        judge.append(int(score))
    agreement = {
        "run": run.name,
        "graded_file": graded_csv.name,
        "n": len(human),
        "cohen_kappa": metrics.cohen_kappa(human, judge),
        "exact_agreement_pct": PERCENT
        * sum(h == j for h, j in zip(human, judge, strict=True))
        / len(human)
        if human
        else None,
    }
    folder = results_dir or Path(settings.EVAL_RESULTS_DIR)
    _write(folder / f"{_stem(f'agreement_{run.name}')}.json", json.dumps(agreement, indent=1))
    return agreement
