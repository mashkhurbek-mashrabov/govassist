from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.evaluation.models import EvalRun
from apps.evaluation.reports import judge_agreement
from apps.evaluation.selectors import get_run


class Command(BaseCommand):
    """Cohen's kappa between human grades and the LLM judge."""

    help = "Compare a graded judge-sample CSV with the judge scores of the run."

    def add_arguments(self, parser: CommandParser) -> None:
        """Declare ``--run`` and ``--csv``.

        Args:
            parser: The argument parser.
        """
        parser.add_argument("--run", required=True, help="Run id or name.")
        parser.add_argument("--csv", required=True, type=Path, help="Graded sample CSV.")

    def handle(self, *args: Any, **options: Any) -> None:
        """Compute, write and print the agreement.

        Args:
            *args: Unused.
            **options: Parsed options.

        Raises:
            CommandError: On an unknown run or an invalid CSV.
        """
        try:
            agreement = judge_agreement(get_run(options["run"]), options["csv"])
        except (EvalRun.DoesNotExist, OSError, ValueError, KeyError) as exc:
            raise CommandError(str(exc)) from exc
        kappa, exact = agreement["cohen_kappa"], agreement["exact_agreement_pct"]
        self.stdout.write(f"n={agreement['n']} kappa={kappa} exact={exact}%")
