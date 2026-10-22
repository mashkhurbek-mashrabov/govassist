"""Corpus document review and lifecycle services."""

from collections.abc import Callable

from django.db import transaction
from django.db.models import QuerySet

from apps.common.models import ReviewStatus
from apps.corpus.models import Chunk, Document
from apps.corpus.tasks import index_document


def _enqueue_callback(doc_id_str: str) -> Callable[[], None]:
    """Build a zero-argument callback for transaction.on_commit."""

    def _callback() -> None:
        index_document.enqueue(doc_id_str)

    return _callback


@transaction.atomic
def approve_documents(queryset: QuerySet[Document]) -> int:
    """Approve documents and enqueue indexing upon transaction commit.

    Args:
        queryset: QuerySet of Document instances to approve.

    Returns:
        Number of documents updated.
    """
    doc_ids = list(queryset.values_list("id", flat=True))
    if not doc_ids:
        return 0

    count = queryset.update(status=ReviewStatus.APPROVED)
    for doc_id in doc_ids:
        transaction.on_commit(_enqueue_callback(str(doc_id)))
    return count


@transaction.atomic
def reject_documents(queryset: QuerySet[Document]) -> int:
    """Reject documents and delete any previously indexed chunks.

    Args:
        queryset: QuerySet of Document instances to reject.

    Returns:
        Number of documents updated.
    """
    doc_ids = list(queryset.values_list("id", flat=True))
    if not doc_ids:
        return 0

    Chunk.objects.filter(document_id__in=doc_ids).delete()
    return queryset.update(status=ReviewStatus.REJECTED)
