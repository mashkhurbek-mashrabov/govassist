from pathlib import Path
from typing import Any

from django.core.management.base import CommandError, CommandParser

from apps.evaluation.management.base import QuestionSetCommand
from apps.evaluation.reports import write_run_report
from apps.evaluation.services import import_external_answers


class Command(QuestionSetCommand):
    """Import transcribed answers of external chatbots as runs and report them."""

    help = "Create one external run per system/prompt style/date from a CSV."

    def add_arguments(self, parser: CommandParser) -> None:
        """Declare ``--file`` and ``--version``.

        Args:
            parser: The argument parser.
        """
        parser.add_argument("--file", required=True, type=Path)
        parser.add_argument("--version", required=True, help="Question-set version.")

    def handle(self, *args: Any, **options: Any) -> None:
        """Import, write each run's report and print the files.

        Args:
            *args: Unused.
            **options: Parsed options.

        Raises:
            CommandError: On an invalid file.
        """
        try:
            runs = import_external_answers(options["file"], options["version"])
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        for run in runs:
            for path in write_run_report(run):
                self.stdout.write(f"Wrote {path}")
