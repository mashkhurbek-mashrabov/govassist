from typing import Any

from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    """Fill missing office phones from the saved pages of one publisher (no requests)."""

    help = "Read phones from saved directory pages (structured data) into offices without one."

    def add_arguments(self, parser: CommandParser) -> None:
        """Declare ``--publisher`` and ``--dry-run``.

        Args:
            parser: The argument parser.
        """
        parser.add_argument("--publisher", required=True, help="e.g. goldenpages.uz")
        parser.add_argument("--dry-run", action="store_true", help="Count only.")

    def handle(self, *args: Any, **options: Any) -> None:
        """Run the backfill and report the counts.

        Args:
            *args: Unused.
            **options: Parsed options.
        """
        from apps.collector.backfill import backfill_phones  # noqa: PLC0415 (worker image)

        result = backfill_phones(options["publisher"], dry_run=options["dry_run"])
        prefix = "Would fill" if options["dry_run"] else "Filled"
        self.stdout.write(
            f"{prefix} {result.filled} of {result.checked} offices; "
            f"{result.no_phone} pages state no phone; {result.no_raw_page} have no saved page."
        )
