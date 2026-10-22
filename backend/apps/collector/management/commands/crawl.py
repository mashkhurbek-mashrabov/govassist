from typing import Any
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.collector import services
from apps.collector.models import CrawlJob, CrawlSource


def find_source(value: str) -> CrawlSource:
    """A source by UUID or exact name.

    Args:
        value: UUID or name.

    Raises:
        CommandError: When no single source matches.
    """
    lookup: dict[str, object]
    try:
        lookup = {"id": UUID(value)}
    except ValueError:
        lookup = {"name": value}
    try:
        return CrawlSource.objects.get(**lookup)
    except CrawlSource.DoesNotExist as exc:
        msg = f"No crawl source {value!r}."
        raise CommandError(msg) from exc


class Command(BaseCommand):
    """Crawl one source now, in this process (no worker needed)."""

    help = "Crawl a source by id or exact name; use --all for every active source."

    def add_arguments(self, parser: CommandParser) -> None:
        """Declare ``--source`` and ``--all``.

        Args:
            parser: The argument parser.
        """
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--source", help="Source UUID or exact name.")
        group.add_argument("--all", action="store_true", help="Every active source.")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-process unchanged pages (after a parser change).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Run the crawl(s), report each job, and fail at the end if any source failed.

        Args:
            *args: Unused.
            **options: Parsed options.

        Raises:
            CommandError: When at least one source failed (the others still ran).
        """
        sources = (
            list(CrawlSource.objects.filter(is_active=True))
            if options["all"]
            else [find_source(options["source"])]
        )
        failed: list[str] = []
        for source in sources:
            job = CrawlJob.objects.create(source=source)
            try:
                services.run_job(job, force=options["force"])
            except Exception as exc:
                failed.append(source.name)
                self.stderr.write(f"{source.name}: failed: {type(exc).__name__}: {exc}")
                continue
            self.stdout.write(
                f"{source.name}: {job.status}, fetched {job.pages_fetched}, "
                f"skipped {job.pages_skipped}"
            )
        if failed:
            msg = f"{len(failed)} source(s) failed: {', '.join(failed)}"
            raise CommandError(msg)
