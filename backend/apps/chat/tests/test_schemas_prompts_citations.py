"""Unit tests for the Answer schema, prompt rendering and citation resolution."""

import json
from typing import Any

import pytest
from pydantic import ValidationError

from apps.chat.citations import resolve_citations
from apps.chat.prompts import ContextBlock, Turn, load_template, render_prompt
from apps.chat.schemas import Answer, ChatRequest
from apps.common.i18n import Lang

FIELD_ORDER = [
    "answer_type",
    "language",
    "title",
    "summary",
    "steps",
    "documents",
    "fee",
    "processing_time",
    "law_points",
    "follow_up_questions",
]


def answer_dict(**overrides: Any) -> dict[str, Any]:
    """A valid NAMUNA service answer with optional overrides."""
    base: dict[str, Any] = {
        "answer_type": "service",
        "language": "uz-Latn",
        "title": "NAMUNA",
        "summary": "NAMUNA qisqa javob.",
        "steps": [{"text": "NAMUNA qadam", "source_ids": ["S1", "S9", "S1"]}],
        "documents": [{"text": "NAMUNA hujjat", "source_ids": ["S2"]}],
        "fee": {"text": "NAMUNA", "source_ids": ["S2"]},
        "processing_time": None,
        "law_points": [{"quote": "NAMUNA", "explanation": "NAMUNA", "source_ids": ["S3"]}],
        "follow_up_questions": ["NAMUNA?"],
    }
    return base | overrides


def test_schema_field_order_and_property_ordering() -> None:
    """The JSON schema keeps the contract order and pins it for Gemini."""
    schema = Answer.model_json_schema()
    assert list(schema["properties"]) == FIELD_ORDER
    assert schema["propertyOrdering"] == FIELD_ORDER
    assert schema["$defs"]["Item"]["propertyOrdering"] == ["text", "source_ids"]


def test_over_long_title_and_lists_are_trimmed() -> None:
    """Title is cut to 80 chars, steps to 7, follow-ups to 3."""
    data = answer_dict(
        title="x" * 100,
        steps=[{"text": str(i), "source_ids": []} for i in range(9)],
        follow_up_questions=["a", "b", "c", "d"],
    )
    answer = Answer.model_validate(data)
    assert len(answer.title) == 80
    assert len(answer.steps) == 7
    assert answer.follow_up_questions == ["a", "b", "c"]


@pytest.mark.parametrize("kind", ["not_found", "off_topic"])
def test_refusals_keep_only_title_summary_followups(kind: str) -> None:
    """Refused answers have empty arrays and null fee/time."""
    answer = Answer.model_validate(answer_dict(answer_type=kind))
    assert answer.refused
    assert (answer.steps, answer.documents, answer.law_points) == ([], [], [])
    assert answer.fee is None
    assert answer.follow_up_questions == ["NAMUNA?"]


def test_unknown_keys_and_missing_fields_fail() -> None:
    """The schema is strict: every field present, nothing extra."""
    with pytest.raises(ValidationError):
        Answer.model_validate(answer_dict(extra="x"))
    data = answer_dict()
    del data["fee"]
    with pytest.raises(ValidationError):
        Answer.model_validate(data)


def test_chat_request_validation() -> None:
    """Text is stripped and required; conversation_id must be a UUID."""
    assert ChatRequest.model_validate({"text": "  hi  "}).text == "hi"
    with pytest.raises(ValidationError):
        ChatRequest.model_validate({"text": "   "})
    with pytest.raises(ValidationError):
        ChatRequest.model_validate({"text": "hi", "conversation_id": "nope"})


def test_render_prompt() -> None:
    """Rules get the language; context, office, history and question are filled in."""
    prompt = render_prompt(
        version="v1",
        language=Lang.UZ_CYRL,
        question="Савол?",
        context=[ContextBlock("S1", "NAMUNA", "lex.uz", "14-modda", "2024-01-01", "Matn {x}")],
        history=[Turn("Oldin?", "Sarlavha", "Xulosa")],
        office_type_label="Davlat xizmatlari markazi",
    )
    assert "Answer in Uzbek (Cyrillic script)" in prompt.system
    assert '"language" to "uz-Cyrl"' in prompt.system
    assert '"the Davlat xizmatlari markazi shown below"' in prompt.system
    assert "[S1] NAMUNA — lex.uz — 14-modda — 2024-01-01\nMatn {x}\n---" in prompt.user
    assert "User: Oldin?\nAssistant: Sarlavha — Xulosa" in prompt.user
    assert prompt.user.endswith("QUESTION\nСавол?")
    assert prompt.sha256 == load_template("v1").sha256
    assert len(prompt.sha256) == 64


def test_render_prompt_without_context_office_or_history() -> None:
    """Empty parts render as (none) and a generic office reference."""
    prompt = render_prompt(
        version="v1",
        language=Lang.EN,
        question="Q?",
        context=[],
        history=[],
        office_type_label=None,
    )
    assert '"the office shown below"' in prompt.system
    assert prompt.user.count("(none)") == 3


def test_resolve_citations() -> None:
    """Unknown ids are dropped, duplicates removed, sources in first-citation order."""
    sources = {label: {"id": label} for label in ("S1", "S2", "S3", "S4")}
    result = resolve_citations(Answer.model_validate(answer_dict()), sources)
    assert result.answer.steps[0].source_ids == ["S1"]
    assert [source["id"] for source in result.sources] == ["S1", "S2", "S3"]
    assert result.cited_labels == {"S1", "S2", "S3"}
    with_time = answer_dict(processing_time={"text": "NAMUNA", "source_ids": ["S4", "S7"]})
    assert resolve_citations(Answer.model_validate(with_time), sources).answer.processing_time
    assert json.loads(result.answer.model_dump_json())["steps"][0]["source_ids"] == ["S1"]
