from typing import Any
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.corpus import indexing


class Command(BaseCommand):
    """Index one document or every approved document without chunks."""

    help = "Chunk and embed approved documents."

    def add_arguments(self, parser: CommandParser) -> None:
        """Declare ``--document`` and ``--all-pending``.

        Args:
            parser: The argument parser.
        """
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--document", type=UUID, help="Document id to (re)index.")
        group.add_argument("--all-pending", action="store_true", help="Approved, not yet indexed.")

    def handle(self, *args: Any, **options: Any) -> None:
        """Run the indexing.

        Args:
            *args: Unused.
            **options: Parsed options.

        Raises:
            CommandError: When a given document was not indexed.
        """
        ids = [options["document"]] if options["document"] else indexing.pending_document_ids()
        for document_id in ids:
            count = indexing.index_document(document_id)
            if options["document"] and count == 0:
                msg = f"Document {document_id} is not approved/active."
                raise CommandError(msg)
            self.stdout.write(f"{document_id}: {count} chunks")
        self.stdout.write(self.style.SUCCESS(f"Indexed {len(ids)} documents."))
