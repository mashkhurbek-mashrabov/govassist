from pathlib import Path
from typing import Any

from django.core.management.base import CommandError, CommandParser

from apps.evaluation.management.base import QuestionSetCommand
from apps.evaluation.services import load_questions


class Command(QuestionSetCommand):
    """Load a question set from JSONL (all or nothing)."""

    help = "Create or update the evaluation questions of a version from a JSONL file."

    def add_arguments(self, parser: CommandParser) -> None:
        """Declare ``--file`` and ``--version``.

        Args:
            parser: The argument parser.
        """
        parser.add_argument("--file", required=True, type=Path)
        parser.add_argument("--version", required=True)

    def handle(self, *args: Any, **options: Any) -> None:
        """Load the file and report the counts.

        Args:
            *args: Unused.
            **options: Parsed options.

        Raises:
            CommandError: On an invalid file.
        """
        try:
            created, updated = load_questions(options["file"], options["version"])
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(f"Questions {options['version']}: {created} created, {updated} updated.")
