"""Evaluation writes: load a question set, import external answers."""

import csv
from pathlib import Path

from django.db import transaction
from django.utils import timezone
from pydantic import ValidationError

from apps.evaluation.constants import RunKind
from apps.evaluation.metrics import text_scores
from apps.evaluation.models import EvalQuestion, EvalResult, EvalRun
from apps.evaluation.schemas import ExternalRow, QuestionRow


def _rows(path: Path) -> list[QuestionRow]:
    """Every non-empty JSONL line validated.

    Raises:
        ValueError: On the first invalid line (its line number and the reason).
    """
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(QuestionRow.model_validate_json(line))
        except ValidationError as exc:
            msg = f"{path.name}:{number}: {exc.errors()[0]['loc']} {exc.errors()[0]['msg']}"
            raise ValueError(msg) from exc
    return rows


@transaction.atomic
def load_questions(path: Path, version: str) -> tuple[int, int]:
    """Create or update the questions of ``version`` from a JSONL file (all or nothing).

    Args:
        path: The JSONL file (one ``QuestionRow`` per line).
        version: The question-set version, e.g. ``v1``.

    Returns:
        (created, updated) counts.

    Raises:
        ValueError: On an invalid line or a duplicate ``qid``.
    """
    rows = _rows(path)
    qids = [row.qid for row in rows]
    if len(qids) != len(set(qids)):
        msg = f"duplicate qid in {path.name}"
        raise ValueError(msg)
    created = 0
    for row in rows:
        data = row.model_dump(exclude={"qid"})
        _, was_created = EvalQuestion.objects.update_or_create(
            version=version, qid=row.qid, defaults=data
        )
        created += was_created
    return created, len(rows) - created


@transaction.atomic
def import_external_answers(path: Path, version: str) -> list[EvalRun]:
    """Store transcribed external chatbot answers as runs, one per system/prompt style/date.

    They are scored with the metrics that apply to plain text (script consistency); the
    judge and the human graders score the rest. Retrieval metrics do not apply.

    Args:
        path: CSV with ``EXTERNAL_COLUMNS`` (+ optional ``system_prompt``).
        version: The question-set version the ``qid`` values belong to.

    Returns:
        The runs created.

    Raises:
        ValueError: On an invalid row or an unknown ``qid``.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        rows = []
        for number, raw in enumerate(csv.DictReader(handle), start=2):
            try:
                rows.append(ExternalRow.model_validate(raw))
            except ValidationError as exc:
                msg = f"{path.name}:{number}: {exc.errors()[0]['loc']} {exc.errors()[0]['msg']}"
                raise ValueError(msg) from exc
    questions = {q.qid: q for q in EvalQuestion.objects.filter(version=version)}
    runs: dict[tuple[str, str, str, str], EvalRun] = {}
    for row in rows:
        question = questions.get(row.qid)
        if question is None:
            msg = f"unknown qid {row.qid!r} for question set {version}"
            raise ValueError(msg)
        key = (row.system, row.model_version, row.prompt_style, row.date.isoformat())
        if key not in runs:
            now = timezone.now()
            runs[key] = EvalRun.objects.create(
                name=f"external-{row.system}-{row.prompt_style}-{row.date.isoformat()}",
                kind=RunKind.EXTERNAL,
                question_version=version,
                config={
                    "system": row.system,
                    "prompt_style": row.prompt_style,
                    "date": row.date.isoformat(),
                    "system_prompt": row.system_prompt,
                    "source_file": path.name,
                },
                model_names={"generator": row.model_version},
                started_at=now,
                finished_at=now,
            )
        EvalResult.objects.create(
            run=runs[key],
            question=question,
            answer={"text": row.answer_text},
            scores=text_scores(question, row.answer_text),
        )
    return list(runs.values())
