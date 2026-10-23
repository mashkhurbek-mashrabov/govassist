"""Unit tests for the ``sources`` answer (issue #35): detection, merging, the card."""

from typing import Any

import pytest

from apps.chat.constants import SOURCES, SOURCES_TEXT
from apps.chat.schemas import Answer, gemini_response_schema
from apps.chat.source_list import merge_sources, sources_answer, sources_request_language
from apps.common.constants import Lang


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("List the sources", Lang.EN),
        ("What sources did you use?", Lang.EN),
        ("sources?", Lang.EN),
        ("Show me your references", Lang.EN),
        ("Manbalarni ko'rsating", Lang.UZ_LATN),
        ("Manbalarni koʻrsating", Lang.UZ_LATN),
        ("Qaysi manbalardan foydalandingiz?", Lang.UZ_LATN),
        ("manbalar", Lang.UZ_LATN),
        ("Манбаларни кўрсатинг", Lang.UZ_CYRL),
        ("манбалар", Lang.UZ_CYRL),
        ("Қайси манбалардан фойдаландингиз?", Lang.UZ_CYRL),
        ("Покажи источники", Lang.RU),
        ("Какие источники ты использовал?", Lang.RU),
        ("Откуда эта информация? Дай ссылки", Lang.RU),
        ("источники", Lang.RU),
    ],
)
def test_detects_requests_for_sources(text: str, language: Lang) -> None:
    """Requests in every language are found, in the language of the matched noun."""
    assert sources_request_language(text) == language


@pytest.mark.parametrize(
    "text",
    [
        "What documents do I need?",
        "Qanday hujjatlar kerak?",
        "Какие документы нужны для прописки?",
        "Қандай ҳужжатлар керак?",
        "What sources of income are taxed?",
        "Daromad manbasini qanday tasdiqlash mumkin?",
        "Какие источники дохода учитываются?",
        "Pasportni qanday almashtiraman?",
        "Rahmat!",
    ],
)
def test_ignores_service_questions(text: str) -> None:
    """Service questions, even with the same nouns, are not source requests."""
    assert sources_request_language(text) is None


def source(url: str, section: str | None, label: str = "S1") -> dict[str, Any]:
    """A NAMUNA contract ``Source``."""
    return {
        "id": label,
        "kind": "law",
        "title": f"NAMUNA {url}",
        "publisher": "example.org",
        "url": url,
        "section": section,
        "published_at": None,
        "fetched_at": "2026-10-01T00:00:00Z",
    }


def test_merge_dedupes_in_first_citation_order_and_relabels() -> None:
    """Earlier answers' sources are merged, deduplicated and relabelled S1..Sn."""
    first = [
        source("https://example.org/a", "1-modda", "S1"),
        source("https://example.org/b", None, "S2"),
    ]
    second = [
        source("https://example.org/b", None, "S1"),
        source("https://example.org/a", "2-modda", "S3"),
    ]
    merged = merge_sources([first, [], second])
    assert [(s["url"], s["section"], s["id"]) for s in merged] == [
        ("https://example.org/a", "1-modda", "S1"),
        ("https://example.org/b", None, "S2"),
        ("https://example.org/a", "2-modda", "S3"),
    ]
    assert first[0]["id"] == "S1" and second[0]["id"] == "S1"  # stored rows are not modified


@pytest.mark.parametrize("found", [True, False])
def test_sources_card(found: bool) -> None:
    """Title and one-sentence summary in the question's language; nothing else; not refused."""
    sources = [source("https://example.org/a", None)] if found else []
    citations = sources_answer(Lang.RU, sources)
    answer = citations.answer
    assert answer.answer_type == SOURCES
    assert answer.language == "ru"
    assert answer.title == SOURCES_TEXT[Lang.RU]["title"]
    assert answer.summary == SOURCES_TEXT[Lang.RU]["found" if found else "empty"]
    assert (answer.steps, answer.documents, answer.law_points, answer.follow_up_questions) == (
        [],
        [],
        [],
        [],
    )
    assert answer.fee is None and answer.processing_time is None
    assert not answer.refused
    assert citations.sources == sources


def test_model_can_never_choose_sources() -> None:
    """The contract schema has ``sources``; the schema sent to Gemini does not."""
    strict = Answer.model_json_schema()["$defs"]["AnswerType"]["enum"]
    sent = gemini_response_schema()["$defs"]["AnswerType"]["enum"]
    assert SOURCES in strict
    assert sent == [value for value in strict if value != SOURCES]
