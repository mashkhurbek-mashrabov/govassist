"""Resolve the model's ``source_ids`` against the retrieval set (plan §11, contract §5)."""

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from apps.chat.schemas import Answer, Item, LawPoint


@dataclass(frozen=True)
class Citations:
    """A cleaned answer plus the sources it cites, in order of first citation."""

    answer: Answer
    sources: list[dict[str, Any]]
    cited_labels: frozenset[str]


def _cited_items(answer: Answer) -> Iterator[Item | LawPoint]:
    """Every item that can cite sources, in Answer field order."""
    yield from answer.steps
    yield from answer.documents
    if answer.fee is not None:
        yield answer.fee
    if answer.processing_time is not None:
        yield answer.processing_time
    yield from answer.law_points


def resolve_citations(answer: Answer, sources_by_label: Mapping[str, dict[str, Any]]) -> Citations:
    """Drop unknown/duplicate ``source_ids`` and list the cited sources.

    Args:
        answer: The validated model answer (not modified).
        sources_by_label: ``"S1"`` → contract ``Source`` dict for the retrieval set.

    Returns:
        The cleaned answer, cited sources (first-citation order, original ``S`` ids) and
        the cited labels.
    """
    cleaned = answer.model_copy(deep=True)
    order: list[str] = []
    for item in _cited_items(cleaned):
        known = [label for label in dict.fromkeys(item.source_ids) if label in sources_by_label]
        item.source_ids = known
        order.extend(label for label in known if label not in order)
    return Citations(
        answer=cleaned,
        sources=[sources_by_label[label] for label in order],
        cited_labels=frozenset(order),
    )
