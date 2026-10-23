from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.evaluation.models import EvalRun
from apps.evaluation.reports import write_comparison
from apps.evaluation.selectors import get_run


class Command(BaseCommand):
    """Compare two runs metric by metric (delta = b − a)."""

    help = "Write a JSON + Markdown comparison of two evaluation runs."

    def add_arguments(self, parser: CommandParser) -> None:
        """Declare the two runs.

        Args:
            parser: The argument parser.
        """
        parser.add_argument("a", help="Baseline run id or name.")
        parser.add_argument("b", help="Compared run id or name.")

    def handle(self, *args: Any, **options: Any) -> None:
        """Write the comparison and print the files.

        Args:
            *args: Unused.
            **options: Parsed options.

        Raises:
            CommandError: When a run is unknown.
        """
        try:
            a, b = get_run(options["a"]), get_run(options["b"])
        except EvalRun.DoesNotExist as exc:
            raise CommandError(str(exc)) from exc
        for path in write_comparison(a, b):
            self.stdout.write(f"Wrote {path}")
