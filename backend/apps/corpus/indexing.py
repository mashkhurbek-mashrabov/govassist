"""Chunk → embed → store for approved documents (plan §5 step 4, §8)."""

import logging
from uuid import UUID

from asgiref.sync import async_to_sync
from django.db import transaction
from django.db.models import QuerySet

from apps.common.models import ReviewStatus
from apps.corpus.chunking import chunk_document
from apps.corpus.embeddings import DocumentInput, Embedder, GeminiEmbedder
from apps.corpus.models import Chunk, Document

logger = logging.getLogger(__name__)


def indexable_documents() -> QuerySet[Document]:
    """Approved, active documents (the only ones used in answers)."""
    return Document.objects.filter(status=ReviewStatus.APPROVED, is_active=True)


def pending_document_ids() -> list[UUID]:
    """Approved, active documents that have no chunks yet."""
    return list(indexable_documents().filter(chunks__isnull=True).values_list("id", flat=True))


def index_document(document_id: UUID, embedder: Embedder | None = None) -> int:
    """Re-chunk and embed one approved document, replacing its old chunks.

    Args:
        document_id: The document to index.
        embedder: Embedding port; Gemini by default.

    Returns:
        Number of chunks stored (0 when the document is not approved/active).
    """
    document = indexable_documents().filter(id=document_id).first()
    if document is None:
        logger.info("Skip indexing: document not approved/active", extra={"id": str(document_id)})
        return 0
    drafts = chunk_document(document.text, lang=document.language)
    inputs = [DocumentInput(document.title, draft.heading_path, draft.text) for draft in drafts]
    vectors = async_to_sync((embedder or GeminiEmbedder()).embed_documents)(inputs)
    chunks = [
        Chunk(
            document=document,
            order=draft.order,
            heading_path=draft.heading_path,
            text=draft.text,
            text_normalized=draft.text_normalized,
            char_count=draft.char_count,
            embedding=vector,
        )
        for draft, vector in zip(drafts, vectors, strict=True)
    ]
    with transaction.atomic():
        document.chunks.all().delete()
        Chunk.objects.bulk_create(chunks)
    logger.info("Indexed document", extra={"id": str(document_id), "chunks": len(chunks)})
    return len(chunks)
