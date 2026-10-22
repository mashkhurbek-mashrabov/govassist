"""Document review: approve (→ index), reject, re-index."""

from collections.abc import Sequence
from functools import partial
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet

from apps.common.models import ReviewStatus
from apps.corpus.models import Chunk, Document


def _enqueue_indexing(document_ids: Sequence[UUID]) -> None:
    """Queue ``index_document`` for each id once the transaction commits."""
    from apps.corpus.tasks import index_document  # noqa: PLC0415 (tasks imports indexing)

    for document_id in document_ids:
        transaction.on_commit(partial(index_document.enqueue, str(document_id)))


@transaction.atomic
def approve_documents(queryset: QuerySet[Document]) -> int:
    """Approve documents and queue their indexing.

    Args:
        queryset: Documents to approve.

    Returns:
        Number approved.
    """
    ids = list(queryset.values_list("id", flat=True))
    count = Document.objects.filter(id__in=ids).update(status=ReviewStatus.APPROVED)
    _enqueue_indexing(ids)
    return count


@transaction.atomic
def reject_documents(queryset: QuerySet[Document]) -> int:
    """Reject documents and delete their chunks, so they are never retrieved.

    Args:
        queryset: Documents to reject.

    Returns:
        Number rejected.
    """
    ids = list(queryset.values_list("id", flat=True))
    Chunk.objects.filter(document_id__in=ids).delete()
    return Document.objects.filter(id__in=ids).update(status=ReviewStatus.REJECTED)


@transaction.atomic
def reindex_documents(queryset: QuerySet[Document]) -> int:
    """Queue re-indexing for the approved documents in ``queryset``.

    Args:
        queryset: Documents to re-index (others are ignored).

    Returns:
        Number queued.
    """
    ids = list(queryset.filter(status=ReviewStatus.APPROVED).values_list("id", flat=True))
    _enqueue_indexing(ids)
    return len(ids)
