"""Tests for hybrid retrieval (FakeEmbedder vectors, real Postgres FTS + pgvector)."""

from uuid import uuid4

import pytest
from asgiref.sync import async_to_sync
from django.test import override_settings
from django.utils import timezone

from apps.common.constants import Lang, ReviewStatus
from apps.common.text import normalize_for_search
from apps.corpus.embeddings import FakeEmbedder
from apps.corpus.models import Chunk, Document
from apps.retrieval.search import _Ranked, diversify, keyword_query, rrf, search

pytestmark = pytest.mark.django_db
EMBEDDER = FakeEmbedder()

NAMUNA_TEXTS = {
    "passport": "NAMUNA pasport almashtirish uchun ariza topshiriladi va davlat boji toʻlanadi",
    "marriage": "NAMUNA nikohni qayd etish FHDYO organida amalga oshiriladi",
    "tax": "NAMUNA soliq deklaratsiyasi har yili topshiriladi",
}


def _vector(text: str) -> list[float]:
    """Embed a text with the fake embedder."""
    return async_to_sync(EMBEDDER.embed_query)(text)


def _document(key: str, *, status: str = ReviewStatus.APPROVED, chunks: int = 1) -> Document:
    """Create a document with ``chunks`` identical NAMUNA chunks."""
    text = NAMUNA_TEXTS[key]
    document = Document.objects.create(
        kind="service_page",
        title=f"NAMUNA {key}",
        url=f"https://example.org/{key}/{uuid4()}",
        publisher="example.org",
        fetched_at=timezone.now(),
        text=text,
        text_hash="x",
        corpus_version="test",
        status=status,
    )
    for order in range(chunks):
        Chunk.objects.create(
            document=document,
            order=order,
            text=text,
            char_count=len(text),
            text_normalized=normalize_for_search(text, Lang.UZ_LATN),
            embedding=_vector(text),
        )
    return document


@pytest.fixture
def corpus() -> dict[str, Document]:
    """Three approved documents and one pending decoy."""
    docs = {key: _document(key) for key in NAMUNA_TEXTS}
    _document("passport", status=ReviewStatus.PENDING)
    return docs


QUESTION = "Pasportni almashtirish uchun nima qilish kerak?"


@pytest.mark.parametrize("mode", ["vector", "keyword", "hybrid"])
def test_each_mode_finds_the_passport_document(mode: str, corpus: dict[str, Document]) -> None:
    """Every mode ranks the passport document first and never returns pending documents."""
    hits = search(QUESTION, Lang.UZ_LATN, query_vector=_vector(QUESTION), mode=mode)  # type: ignore[arg-type]
    assert hits[0].document_id == corpus["passport"].id
    assert hits[0].rank == 1
    approved = {doc.id for doc in corpus.values()}
    assert {hit.document_id for hit in hits} <= approved


def test_hybrid_reports_both_scores(corpus: dict[str, Document]) -> None:
    """Hybrid hits carry vector, keyword and fused scores."""
    top = search(QUESTION, Lang.UZ_LATN, query_vector=_vector(QUESTION))[0]
    assert top.vector_score is not None
    assert top.keyword_score is not None
    assert top.fused_score == pytest.approx(2 / 61)


def test_cyrillic_query_matches_latin_corpus(corpus: dict[str, Document]) -> None:
    """Normalization lets a Cyrillic Uzbek question hit Latin text."""
    hits = search("Паспорт алмаштириш", Lang.UZ_CYRL, mode="keyword")
    assert hits[0].document_id == corpus["passport"].id
    assert not search("Паспорт алмаштириш", Lang.UZ_CYRL, mode="keyword", normalize=False)


def test_vector_mode_needs_a_vector() -> None:
    """Vector and hybrid modes refuse to run without an embedding."""
    with pytest.raises(ValueError, match="query_vector"):
        search(QUESTION, Lang.UZ_LATN)


def test_empty_keyword_query(corpus: dict[str, Document]) -> None:
    """Punctuation-only questions give no keyword hits."""
    assert search("?!", Lang.UZ_LATN, mode="keyword") == []


@override_settings(RAG_MAX_PER_DOC=2, RAG_FINAL_K=5)
def test_diversification_caps_chunks_per_document(db: None) -> None:
    """At most RAG_MAX_PER_DOC chunks of one document are kept."""
    document = _document("passport", chunks=4)
    hits = search(QUESTION, Lang.UZ_LATN, query_vector=_vector(QUESTION))
    assert [hit.document_id for hit in hits] == [document.id, document.id]


def test_k_overrides_final_count(corpus: dict[str, Document]) -> None:
    """``k`` limits the number of hits."""
    assert len(search(QUESTION, Lang.UZ_LATN, query_vector=_vector(QUESTION), k=1)) == 1


def test_rrf_and_diversify_units() -> None:
    """RRF sums reciprocal ranks; diversify keeps order under the cap."""
    a, b, c, d1, d2 = uuid4(), uuid4(), uuid4(), uuid4(), uuid4()
    fused = rrf([_Ranked(a, d1, 0.9), _Ranked(b, d1, 0.8)], [_Ranked(b, d1, 3.0)], k=60)
    assert [chunk for chunk, _ in fused] == [b, a]
    assert fused[0][1] == pytest.approx(1 / 62 + 1 / 61)
    kept = diversify([a, b, c], doc_of={a: d1, b: d1, c: d2}, max_per_doc=1)
    assert kept == [a, c]
    assert keyword_query("pasport  ariza") == "pasport or ariza"
