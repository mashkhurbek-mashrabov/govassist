import asyncio
from typing import Any

from django.conf import settings
from django.core.management.base import CommandError, CommandParser

from apps.evaluation.constants import MODES, NORAG_PROMPT, ON_OFF
from apps.evaluation.judge import OpenAICompatibleJudge
from apps.evaluation.management.base import QuestionSetCommand
from apps.evaluation.reports import write_run_report
from apps.evaluation.runner import EvalConfig, Pipeline, run_eval


def build_pipeline(*, judge: bool) -> tuple[Pipeline, Any]:
    """Gemini embedder and generator on one client, plus the env judge when asked.

    Args:
        judge: Use the judge from ``JUDGE_*`` settings.

    Returns:
        The pipeline and the Gemini client (to close afterwards).
    """
    from apps.chat.generator import GeminiAnswerGenerator  # noqa: PLC0415 (Gemini only here)
    from apps.common.gemini import get_client  # noqa: PLC0415
    from apps.corpus.embeddings import GeminiEmbedder  # noqa: PLC0415

    client = get_client()
    pipeline = Pipeline(
        embedder=GeminiEmbedder(client),
        generator_factory=lambda: GeminiAnswerGenerator(client),
        judge=OpenAICompatibleJudge.from_settings() if judge else None,
    )
    return pipeline, client


class Command(QuestionSetCommand):
    """Run a question set through GovAssist with ablation switches; write the report."""

    help = "Evaluate a question set (vector|keyword|hybrid, normalize on|off, rag on|off)."

    def add_arguments(self, parser: CommandParser) -> None:
        """Declare the run name, question version and switches.

        Args:
            parser: The argument parser.
        """
        parser.add_argument("--name", required=True)
        parser.add_argument("--version", required=True, help="Question-set version.")
        parser.add_argument("--mode", choices=MODES, default="hybrid")
        parser.add_argument("--normalize", choices=tuple(ON_OFF), default="on")
        parser.add_argument("--rag", choices=tuple(ON_OFF), default="on")
        parser.add_argument("--prompt", default=settings.PROMPT_VERSION)
        parser.add_argument("--judge", choices=("none", "env"), default="none")

    def handle(self, *args: Any, **options: Any) -> None:
        """Run, report and print the written files.

        Args:
            *args: Unused.
            **options: Parsed options.

        Raises:
            CommandError: On inconsistent switches or an empty question set.
        """
        rag = ON_OFF[options["rag"]]
        if not rag and options["prompt"] != NORAG_PROMPT:
            msg = f"--rag off needs --prompt {NORAG_PROMPT} (the prompt without context)."
            raise CommandError(msg)
        config = EvalConfig(
            mode=options["mode"],
            normalize=ON_OFF[options["normalize"]],
            rag=rag,
            prompt_version=options["prompt"],
        )
        pipeline, client = build_pipeline(judge=options["judge"] == "env")

        async def go() -> Any:
            """Run on one event loop and close the Gemini client there."""
            try:
                return await run_eval(
                    name=options["name"],
                    version=options["version"],
                    config=config,
                    pipeline=pipeline,
                    git_sha=settings.GIT_SHA,
                )
            finally:
                await client.aio.aclose()
                client.close()

        try:
            run = asyncio.run(go())
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        for path in write_run_report(run):
            self.stdout.write(f"Wrote {path}")
