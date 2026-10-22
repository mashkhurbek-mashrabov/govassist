import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from apps.chat.schemas import Answer

FILE_NAME = "answer.schema.json"


def answer_schema_json() -> str:
    """The Answer JSON schema as written to ``docs/schema`` (stable, sorted-free order)."""
    return json.dumps(Answer.model_json_schema(), ensure_ascii=False, indent=2) + "\n"


class Command(BaseCommand):
    """Write ``answer.schema.json`` (the schema Gemini gets as ``response_schema``)."""

    help = "Export the Answer JSON schema to a directory."

    def add_arguments(self, parser: CommandParser) -> None:
        """Declare the output directory.

        Args:
            parser: The argument parser.
        """
        parser.add_argument("directory", type=Path)

    def handle(self, *args: Any, **options: Any) -> None:
        """Write the file.

        Args:
            *args: Unused.
            **options: Parsed options.
        """
        directory: Path = options["directory"]
        directory.mkdir(parents=True, exist_ok=True)
        (directory / FILE_NAME).write_text(answer_schema_json(), encoding="utf-8")
        self.stdout.write(f"Wrote {directory / FILE_NAME}")
