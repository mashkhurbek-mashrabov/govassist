"""Tests for question loading, external imports, reports and the management commands."""

import csv
import json
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from apps.chat.generator import FakeAnswerGenerator
from apps.corpus.embeddings import FakeEmbedder
from apps.evaluation.constants import HUMAN_COLUMN, JUDGE_CORRECTNESS, RECALL, SCRIPT, RunKind
from apps.evaluation.judge import FakeJudge
from apps.evaluation.management.commands import run_eval as run_eval_command
from apps.evaluation.models import EvalQuestion, EvalResult, EvalRun
from apps.evaluation.reports import (
    judge_agreement,
    write_comparison,
    write_judge_sample,
    write_run_report,
)
from apps.evaluation.runner import Pipeline
from apps.evaluation.selectors import get_run
from apps.evaluation.services import import_external_answers, load_questions
from conftest import answer_json

pytestmark = pytest.mark.django_db(transaction=True)

SAMPLE = Path(__file__).resolve().parents[1] / "fixtures" / "questions_namuna.jsonl"


@pytest.fixture
def results_dir(tmp_path: Path) -> Iterator[Path]:
    """Write reports into a temp folder, never into docs/results."""
    folder = tmp_path / "results"
    with override_settings(EVAL_RESULTS_DIR=folder):
        yield folder


@pytest.fixture
def questions() -> list[EvalQuestion]:
    """The committed NAMUNA sample, loaded as version ``v0``."""
    load_questions(SAMPLE, "v0")
    return list(EvalQuestion.objects.filter(version="v0"))


def make_run(
    name: str, items: list[EvalQuestion], *, correctness: int = 2, recall: float = 1.0
) -> EvalRun:
    """A finished run with one scored result per question (stored directly, no pipeline)."""
    eval_run = EvalRun.objects.create(name=name, question_version="v0")
    for item in items:
        EvalResult.objects.create(
            run=eval_run,
            question=item,
            answer={"title": "NAMUNA", "summary": "NAMUNA javob."},
            scores={RECALL: recall, SCRIPT: True, JUDGE_CORRECTNESS: correctness},
            latency_ms=100,
            prompt_tokens=10,
            completion_tokens=5,
        )
    return eval_run


def write_lines(path: Path, *lines: str) -> Path:
    """Write ``lines`` to ``path`` and return it."""
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_load_sample_is_idempotent() -> None:
    """The sample has 5 questions; loading it again updates them in place."""
    assert load_questions(SAMPLE, "v0") == (5, 0)
    assert load_questions(SAMPLE, "v0") == (0, 5)
    assert EvalQuestion.objects.filter(version="v0", qid__startswith="NAMUNA").count() == 5


def test_load_rejects_bad_and_duplicate_lines(tmp_path: Path) -> None:
    """Errors name the line; nothing is saved."""
    line = SAMPLE.read_text(encoding="utf-8").splitlines()[0]
    with pytest.raises(ValueError, match="duplicate qid"):
        load_questions(write_lines(tmp_path / "dup.jsonl", line, line), "v0")
    bad = json.dumps(json.loads(line) | {"category": "nope"})
    with pytest.raises(ValueError, match=":1:"):
        load_questions(write_lines(tmp_path / "bad.jsonl", bad), "v0")
    assert not EvalQuestion.objects.exists()


def test_run_report_files_are_never_overwritten(
    questions: list[EvalQuestion], results_dir: Path
) -> None:
    """JSON, Markdown and CSV are written; a second write in the same second fails loudly."""
    eval_run = make_run("base", questions)
    paths = write_run_report(eval_run)
    assert sorted(path.suffix for path in paths) == [".csv", ".json", ".md"]
    summary = json.loads(paths[0].read_text(encoding="utf-8"))
    assert summary["overall"]["questions"] == 5
    assert summary["overall"][RECALL] == 1.0
    assert set(summary["groups"]["language"]) == {"en", "ru", "uz-Cyrl", "uz-Latn"}
    with pytest.raises(FileExistsError):
        write_run_report(eval_run)


def test_comparison_deltas(questions: list[EvalQuestion], results_dir: Path) -> None:
    """Deltas are b − a, overall and per group."""
    a, b = make_run("a", questions, recall=0.5), make_run("b", questions, recall=1.0)
    json_path, md_path = write_comparison(a, b)
    result = json.loads(json_path.read_text(encoding="utf-8"))
    assert result["overall"][RECALL]["delta"] == 0.5
    assert result["groups"]["script"]["latn"][RECALL] == 0.5
    assert "delta" in md_path.read_text(encoding="utf-8")


def test_judge_sample_and_agreement(questions: list[EvalQuestion], results_dir: Path) -> None:
    """The sample is blind and reproducible; κ is computed from the filled-in grades."""
    eval_run = make_run("judged", questions[:4])
    for result, correctness in zip(
        EvalResult.objects.filter(run=eval_run).order_by("id"), (0, 1, 2, 2), strict=True
    ):
        result.scores = {JUDGE_CORRECTNESS: correctness}
        result.save()
    path = write_judge_sample(eval_run, n=4, seed=42)
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    assert HUMAN_COLUMN in rows[0]
    assert "scores" not in rows[0]
    assert "judged" not in rows[0].values()
    judged = {
        str(r.id): r.scores[JUDGE_CORRECTNESS] for r in EvalResult.objects.filter(run=eval_run)
    }
    for row in rows:
        row[HUMAN_COLUMN] = str(judged[row["result_id"]])
    graded = results_dir / "graded.csv"
    with graded.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    agreement = judge_agreement(eval_run, graded)
    assert agreement == {
        "run": "judged",
        "graded_file": "graded.csv",
        "n": 4,
        "cohen_kappa": 1.0,
        "exact_agreement_pct": 100.0,
    }


def test_agreement_rejects_bad_grades(questions: list[EvalQuestion], results_dir: Path) -> None:
    """A grade outside 0..2 or an unknown result id is an error."""
    eval_run = make_run("judged", questions[:1])
    result_id = str(EvalResult.objects.get(run=eval_run).id)
    graded = write_lines(
        results_dir.parent / "g.csv", f"result_id,{HUMAN_COLUMN}", f"{result_id},5"
    )
    with pytest.raises(ValueError, match="0, 1 or 2"):
        judge_agreement(eval_run, graded)
    unknown = write_lines(results_dir.parent / "u.csv", f"result_id,{HUMAN_COLUMN}", "nope,1")
    with pytest.raises(ValueError, match="not a judged answer"):
        judge_agreement(eval_run, unknown)


def test_import_external_answers(questions: list[EvalQuestion], tmp_path: Path) -> None:
    """One run per system/prompt style/date, scored with the plain-text metrics."""
    header = "qid,system,model_version,prompt_style,date,answer_text"
    path = write_lines(
        tmp_path / "external.csv",
        header,
        "NAMUNA-001,chatbot-c,model-1,naive,2026-10-01,NAMUNA ID-karta uchun ariza bering.",
        "NAMUNA-002,chatbot-c,model-1,naive,2026-10-01,NAMUNA ID-karta uchun ariza bering.",
        "NAMUNA-001,chatbot-c,model-1,expert,2026-10-01,NAMUNA javob.",
    )
    runs = import_external_answers(path, "v0")
    assert len(runs) == 2
    naive = next(r for r in runs if r.config["prompt_style"] == "naive")
    assert naive.kind == RunKind.EXTERNAL
    scores = dict(EvalResult.objects.filter(run=naive).values_list("question__qid", "scores"))
    assert scores["NAMUNA-001"][SCRIPT] is True
    assert scores["NAMUNA-002"][SCRIPT] is False  # Cyrillic question, Latin answer
    bad = write_lines(tmp_path / "bad.csv", header, "NAMUNA-999,c,m,naive,2026-10-01,x")
    with pytest.raises(ValueError, match="unknown qid"):
        import_external_answers(bad, "v0")


def test_get_run_by_id_or_newest_name(questions: list[EvalQuestion]) -> None:
    """Runs are found by UUID or by name (newest first)."""
    older, newer = make_run("same", []), make_run("same", [])
    assert get_run(str(older.id)) == older
    assert get_run("same") == newer
    with pytest.raises(EvalRun.DoesNotExist):
        get_run("missing")


def fake_pipeline(*, judge: bool) -> tuple[Pipeline, Any]:
    """The run_eval command's pipeline, faked (no Gemini client)."""

    async def aclose() -> None:
        """Nothing to close."""

    client = SimpleNamespace(aio=SimpleNamespace(aclose=aclose), close=lambda: None)
    pipeline = Pipeline(
        embedder=FakeEmbedder(),
        generator_factory=lambda: FakeAnswerGenerator(answer_json()),
        judge=FakeJudge() if judge else None,
    )
    return pipeline, client


def test_commands_end_to_end(
    results_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Load → run_eval (fakes) → compare → sample → agreement, all through call_command."""
    monkeypatch.setattr(run_eval_command, "build_pipeline", fake_pipeline)
    call_command("load_eval_questions", file=SAMPLE, version="v0")
    call_command("run_eval", name="a", version="v0", mode="keyword", normalize="off", judge="env")
    call_command("run_eval", name="b", version="v0", rag="off", prompt="v3-norag")
    assert EvalResult.objects.filter(run__name="a").count() == 5
    assert get_run("a").config["normalize"] is False
    call_command("compare_runs", "a", "b")
    call_command("export_judge_sample", run="a", n=2, seed=1)
    sample = next(results_dir.glob("*judge_sample_a_n2_seed1.csv"))
    rows = list(csv.DictReader(sample.open(encoding="utf-8", newline="")))
    graded = write_lines(
        tmp_path / "graded.csv",
        f"result_id,{HUMAN_COLUMN}",
        *(f"{row['result_id']},2" for row in rows),
    )
    call_command("judge_agreement", run="a", csv=graded)
    written = {path.suffix for path in results_dir.iterdir()}
    assert written == {".json", ".md", ".csv"}


@pytest.mark.parametrize(
    ("command", "options"),
    [
        ("run_eval", {"name": "x", "version": "v0", "rag": "off"}),
        ("compare_runs", {"a": "missing", "b": "missing"}),
        ("export_judge_sample", {"run": "missing"}),
        ("export_judge_sample", {"run": "missing", "n": 0}),
        ("judge_agreement", {"run": "missing", "csv": Path("missing.csv")}),
        ("load_eval_questions", {"file": Path("missing.jsonl"), "version": "v0"}),
        ("import_external_answers", {"file": Path("missing.csv"), "version": "v0"}),
    ],
)
def test_command_errors(
    command: str, options: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Bad input ends in a CommandError (rag off with the RAG prompt is refused before any call)."""
    monkeypatch.setattr(run_eval_command, "build_pipeline", fake_pipeline)
    positional = [options.pop(key) for key in ("a", "b") if key in options]
    with pytest.raises(CommandError):
        call_command(command, *positional, **options)
