"""Long legal codes: heading paths over 500 characters are stored in full."""

import pytest

from apps.common.constants import ReviewStatus
from apps.corpus.embeddings import FakeEmbedder
from apps.corpus.indexing import index_document
from apps.corpus.models import Chunk
from conftest import namuna_document

pytestmark = pytest.mark.django_db
LONG_TITLE = "NAMUNA " + "juda uzun bo‘lim nomi " * 15


def test_heading_paths_longer_than_500_chars_are_indexed() -> None:
    """The Labour Code has part › paragraph › article paths of 505–526 chars (was varchar 500)."""
    text = f"# {LONG_TITLE}\n\n## {LONG_TITLE}\n\n### 1-modda. NAMUNA\n\nNAMUNA modda matni."
    document = namuna_document(text, kind="law", slug="long")
    document.status = ReviewStatus.APPROVED
    document.save(update_fields=["status"])
    assert index_document(document.id, embedder=FakeEmbedder()) >= 1
    longest = max(Chunk.objects.filter(document=document), key=lambda c: len(c.heading_path))
    assert len(longest.heading_path) > 500
    assert longest.heading_path.endswith("1-modda. NAMUNA")
