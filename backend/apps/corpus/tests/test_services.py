"""Tests for corpus document approval and rejection services."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from django.test import TestCase

from apps.common.constants import ReviewStatus
from apps.corpus.constants import DocumentKind
from apps.corpus.models import Chunk, Document
from apps.corpus.services import approve_documents, reindex_documents, reject_documents


@pytest.mark.django_db
class DocumentServicesTest(TestCase):
    """Test suite for corpus document lifecycle services."""

    def setUp(self) -> None:
        """Create sample test documents and chunks."""
        self.doc = Document.objects.create(
            title="NAMUNA Document",
            url="https://example.uz/doc1",
            publisher="stat.uz",
            text="NAMUNA corpus text",
            text_hash="hash1",
            corpus_version="2026.10",
            fetched_at=datetime.now(UTC),
            status=ReviewStatus.PENDING,
            kind=DocumentKind.LAW,
        )
        self.chunk = Chunk.objects.create(
            document=self.doc,
            order=0,
            heading_path="Heading",
            text="NAMUNA chunk text",
            text_normalized="namuna chunk text",
            char_count=17,
        )

    def test_approve_documents(self) -> None:
        """Verifies approving documents updates status and enqueues indexing."""
        with patch("apps.corpus.tasks.index_document") as mock_task:
            with self.captureOnCommitCallbacks(execute=True):
                count = approve_documents(Document.objects.filter(id=self.doc.id))

            assert count == 1
            self.doc.refresh_from_db()
            assert self.doc.status == ReviewStatus.APPROVED
            mock_task.enqueue.assert_called_once_with(str(self.doc.id))

    def test_reject_documents(self) -> None:
        """Verifies rejecting documents updates status and removes existing chunks."""
        count = reject_documents(Document.objects.filter(id=self.doc.id))
        assert count == 1
        self.doc.refresh_from_db()
        assert self.doc.status == ReviewStatus.REJECTED
        assert not Chunk.objects.filter(document=self.doc).exists()

    def test_empty_queryset(self) -> None:
        """Verifies empty querysets return 0 without errors."""
        empty_qs = Document.objects.none()
        assert approve_documents(empty_qs) == 0
        assert reject_documents(empty_qs) == 0

    def test_reindex_only_approved(self) -> None:
        """Re-index queues approved documents only."""
        with patch("apps.corpus.tasks.index_document") as mock_task:
            with self.captureOnCommitCallbacks(execute=True):
                assert reindex_documents(Document.objects.all()) == 0
                Document.objects.update(status=ReviewStatus.APPROVED)
                assert reindex_documents(Document.objects.all()) == 1
            mock_task.enqueue.assert_called_once_with(str(self.doc.id))
