"""Background jobs for the corpus (run by ``db_worker``)."""

from uuid import UUID

from django.tasks import task

from apps.corpus import indexing


@task
def index_document(document_id: str) -> int:
    """Chunk and embed one approved document.

    Args:
        document_id: The document's UUID as a string (task args must be JSON).

    Returns:
        Number of chunks stored.
    """
    return indexing.index_document(UUID(document_id))
