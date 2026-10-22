"""Hybrid retrieval: pgvector cosine + Postgres full-text, fused with RRF (plan §9).

``mode`` and ``normalize`` exist for the evaluation ablations (RQ3).
"""

import logging
import time
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, QuerySet
from pgvector.django import CosineDistance

from apps.common.models import ReviewStatus
from apps.common.text import normalize_for_search
from apps.corpus.models import SEARCH_CONFIG, Chunk

logger = logging.getLogger(__name__)

type Mode = Literal["vector", "keyword", "hybrid"]
MS_PER_S = 1000


@dataclass(frozen=True)
class Hit:
    """One retrieved chunk with its scores."""

    chunk_id: UUID
    document_id: UUID
    vector_score: float | None
    keyword_score: float | None
    fused_score: float
    rank: int


@dataclass(frozen=True)
class _Ranked:
    """A chunk's position in one ranked list."""

    chunk_id: UUID
    document_id: UUID
    score: float


def _live_chunks() -> QuerySet[Chunk]:
    """Chunks of approved, active documents (the only ones used in answers)."""
    return Chunk.objects.filter(document__status=ReviewStatus.APPROVED, document__is_active=True)


def vector_search(query_vector: Sequence[float], limit: int) -> list[_Ranked]:
    """Top chunks by cosine similarity (HNSW index).

    Args:
        query_vector: The embedded question.
        limit: How many to return.
    """
    rows = (
        _live_chunks()
        .filter(embedding__isnull=False)
        .annotate(distance=CosineDistance("embedding", list(query_vector)))
        .order_by("distance")
        .values_list("id", "document_id", "distance")[:limit]
    )
    return [_Ranked(chunk_id, doc_id, 1.0 - distance) for chunk_id, doc_id, distance in rows]


def keyword_query(text: str) -> str:
    """Build a websearch query that matches ANY of the words (OR), not all of them.

    Args:
        text: Normalized question text.
    """
    return " or ".join(text.split())


def keyword_search(query_text: str, limit: int) -> list[_Ranked]:
    """Top chunks by full-text rank over ``text_normalized``.

    Args:
        query_text: The (normalized) question.
        limit: How many to return.
    """
    terms = keyword_query(query_text)
    if not terms:
        return []
    query = SearchQuery(terms, config=SEARCH_CONFIG, search_type="websearch")
    rows = (
        _live_chunks()
        .filter(search_vector=query)
        .annotate(score=SearchRank(F("search_vector"), query))
        .order_by("-score", "id")
        .values_list("id", "document_id", "score")[:limit]
    )
    return [_Ranked(chunk_id, doc_id, score) for chunk_id, doc_id, score in rows]


def rrf(*ranked_lists: Sequence[_Ranked], k: int) -> list[tuple[UUID, float]]:
    """Reciprocal Rank Fusion: ``Σ 1/(k + rank)`` over the lists (rank is 1-based).

    Args:
        *ranked_lists: Best-first lists.
        k: The RRF constant (60).

    Returns:
        ``(chunk_id, fused_score)`` best first; ties keep first-seen order.
    """
    scores: dict[UUID, float] = defaultdict(float)
    for ranked in ranked_lists:
        for position, item in enumerate(ranked, start=1):
            scores[item.chunk_id] += 1.0 / (k + position)
    return sorted(scores.items(), key=lambda pair: pair[1], reverse=True)


def diversify[T](items: Iterable[T], *, doc_of: dict[T, UUID], max_per_doc: int) -> list[T]:
    """Keep the order but at most ``max_per_doc`` items per document.

    Args:
        items: Best-first chunk ids.
        doc_of: Chunk id → document id.
        max_per_doc: The per-document cap.
    """
    taken: dict[UUID, int] = defaultdict(int)
    kept: list[T] = []
    for item in items:
        document_id = doc_of[item]
        if taken[document_id] < max_per_doc:
            taken[document_id] += 1
            kept.append(item)
    return kept


def search(
    query: str,
    lang: str,
    *,
    query_vector: Sequence[float] | None = None,
    mode: Mode = "hybrid",
    normalize: bool = True,
    k: int | None = None,
) -> list[Hit]:
    """Retrieve the best chunks for a question.

    Args:
        query: The scrubbed question.
        lang: Its detected ``Lang``.
        query_vector: The question embedding (required for vector and hybrid modes).
        mode: ``vector``, ``keyword`` or ``hybrid``.
        normalize: Normalize the keyword query (Cyrillic→Latin, canonicalize).
        k: Final number of hits (default ``RAG_FINAL_K``).

    Returns:
        Best-first hits with 1-based ranks.

    Raises:
        ValueError: When a vector mode is asked without ``query_vector``.
    """
    started = time.perf_counter()
    if mode != "keyword" and query_vector is None:
        msg = f"mode={mode!r} needs query_vector."
        raise ValueError(msg)
    vector = (
        vector_search(query_vector or [], settings.RAG_TOP_K_VECTOR) if mode != "keyword" else []
    )
    query_text = normalize_for_search(query, lang) if normalize else query
    keyword = keyword_search(query_text, settings.RAG_TOP_K_KEYWORD) if mode != "vector" else []

    by_id = {item.chunk_id: item for item in (*keyword, *vector)}
    vector_scores = {item.chunk_id: item.score for item in vector}
    keyword_scores = {item.chunk_id: item.score for item in keyword}
    fused = dict(rrf(vector, keyword, k=settings.RAG_RRF_K))
    doc_of = {chunk_id: item.document_id for chunk_id, item in by_id.items()}
    kept = diversify(fused, doc_of=doc_of, max_per_doc=settings.RAG_MAX_PER_DOC)
    hits = [
        Hit(
            chunk_id=chunk_id,
            document_id=doc_of[chunk_id],
            vector_score=vector_scores.get(chunk_id),
            keyword_score=keyword_scores.get(chunk_id),
            fused_score=fused[chunk_id],
            rank=rank,
        )
        for rank, chunk_id in enumerate(kept[: k or settings.RAG_FINAL_K], start=1)
    ]
    elapsed_ms = int((time.perf_counter() - started) * MS_PER_S)
    logger.info("Retrieval done", extra={"mode": mode, "hits": len(hits), "ms": elapsed_ms})
    return hits
