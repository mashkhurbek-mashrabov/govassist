from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.evaluation.constants import SAMPLE_DEFAULT_N, SAMPLE_DEFAULT_SEED
from apps.evaluation.models import EvalRun
from apps.evaluation.reports import write_judge_sample
from apps.evaluation.selectors import get_run


class Command(BaseCommand):
    """Export a blind random sample of answers for human grading."""

    help = "Write a CSV of N random answers of a run with an empty human_correctness column."

    def add_arguments(self, parser: CommandParser) -> None:
        """Declare ``--run``, ``--n`` and ``--seed``.

        Args:
            parser: The argument parser.
        """
        parser.add_argument("--run", required=True, help="Run id or name.")
        parser.add_argument("--n", type=int, default=SAMPLE_DEFAULT_N)
        parser.add_argument("--seed", type=int, default=SAMPLE_DEFAULT_SEED)

    def handle(self, *args: Any, **options: Any) -> None:
        """Write the sample and print its path.

        Args:
            *args: Unused.
            **options: Parsed options.

        Raises:
            CommandError: When the run is unknown or ``--n`` is not positive.
        """
        if options["n"] < 1:
            raise CommandError("--n must be at least 1.")
        try:
            run = get_run(options["run"])
        except EvalRun.DoesNotExist as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(f"Wrote {write_judge_sample(run, options['n'], options['seed'])}")
