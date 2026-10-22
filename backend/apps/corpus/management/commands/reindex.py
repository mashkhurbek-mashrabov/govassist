from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from apps.corpus import indexing


class Command(BaseCommand):
    """Re-embed every approved document (after an approved model/dimension change)."""

    help = "Re-chunk and re-embed all approved documents."

    def add_arguments(self, parser: CommandParser) -> None:
        """Require ``--all`` so a reindex is never accidental.

        Args:
            parser: The argument parser.
        """
        parser.add_argument("--all", action="store_true", required=True)

    def handle(self, *args: Any, **options: Any) -> None:
        """Reindex all approved documents.

        Args:
            *args: Unused.
            **options: Parsed options.
        """
        ids = list(indexing.indexable_documents().values_list("id", flat=True))
        total = sum(indexing.index_document(document_id) for document_id in ids)
        self.stdout.write(self.style.SUCCESS(f"Reindexed {len(ids)} documents, {total} chunks."))
