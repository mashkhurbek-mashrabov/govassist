"""``answer_type: "sources"``: list the conversation's cited sources (issue #35, contract v1.11).

Built without a corpus search or the LLM: detection is rule-based and the answer is assembled
from the ``sources`` stored on the conversation's earlier assistant messages.
"""

from collections.abc import Iterable, Sequence
from typing import Any

from apps.chat.citations import Citations
from apps.chat.constants import (
    SOURCE_FALSE_FRIENDS,
    SOURCE_NOUNS,
    SOURCE_REQUEST_CUES,
    SOURCES,
    SOURCES_SHORT_REQUEST_WORDS,
    SOURCES_TEXT,
)
from apps.chat.schemas import Answer
from apps.common.constants import Lang
from apps.common.text import canonicalize


def sources_request_language(text: str) -> Lang | None:
    """The language of a request for the conversation's sources, or None for other messages.

    Every language's patterns are checked, and the matched noun sets the language: short
    messages such as "manbalar" are often detected as another language. Questions that only
    use the nouns ("What documents do I need?", "sources of income") do not match.

    Args:
        text: The (scrubbed) user message.
    """
    canonical = canonicalize(text)
    if SOURCE_FALSE_FRIENDS.search(canonical):
        return None
    language = next((lang for lang, noun in SOURCE_NOUNS.items() if noun.search(canonical)), None)
    if language is None:
        return None
    is_short = len(canonical.split()) <= SOURCES_SHORT_REQUEST_WORDS
    return language if is_short or SOURCE_REQUEST_CUES.search(canonical) else None


def _key(source: dict[str, Any]) -> tuple[str, str | None]:
    """A source's identity: the document URL plus the cited section."""
    return source["url"], source.get("section")


def merge_sources(per_answer: Iterable[Sequence[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Deduplicate the cited sources in first-citation order and relabel them ``S1..Sn``.

    Args:
        per_answer: Each earlier answer's stored ``sources``, oldest answer first.
    """
    unique: dict[tuple[str, str | None], dict[str, Any]] = {}
    for sources in per_answer:
        for source in sources:
            unique.setdefault(_key(source), source)
    return [source | {"id": f"S{rank}"} for rank, source in enumerate(unique.values(), start=1)]


def sources_answer(language: Lang, sources: list[dict[str, Any]]) -> Citations:
    """The ``sources`` answer card: localized title and summary, every other field empty.

    Args:
        language: The question's language.
        sources: The merged, relabelled sources (may be empty).

    Returns:
        The answer with its sources; nothing in the card itself cites them.
    """
    text = SOURCES_TEXT[language]
    answer = Answer.model_validate(
        {
            "answer_type": SOURCES,
            "language": language.value,
            "title": text["title"],
            "summary": text["found"] if sources else text["empty"],
            "steps": [],
            "documents": [],
            "fee": None,
            "processing_time": None,
            "law_points": [],
            "follow_up_questions": [],
        }
    )
    return Citations(answer=answer, sources=sources, cited_labels=frozenset())
