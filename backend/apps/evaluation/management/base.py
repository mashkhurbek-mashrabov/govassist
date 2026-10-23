from typing import Any

from django.core.management.base import BaseCommand, CommandParser


class QuestionSetCommand(BaseCommand):
    """A command whose ``--version`` names the question set, replacing Django's own flag."""

    def create_parser(self, prog_name: str, subcommand: str, **kwargs: Any) -> CommandParser:
        """Let ``--version`` declared by the command win over Django's ``--version``.

        Args:
            prog_name: Program name.
            subcommand: Command name.
            **kwargs: Passed to the parser.
        """
        return super().create_parser(prog_name, subcommand, conflict_handler="resolve", **kwargs)
