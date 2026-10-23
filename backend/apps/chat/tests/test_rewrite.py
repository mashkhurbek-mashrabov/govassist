"""Unit tests for the follow-up query rewrite (issue #34), with a fake rewriter."""

import asyncio

import pytest

from apps.chat.constants import REWRITE_MAX_CHARS, REWRITE_PROMPT_VERSION
from apps.chat.generator import FakeQueryRewriter, Usage
from apps.chat.prompts import Prompt, Turn, load_template
from apps.chat.rewrite import clean_query, standalone_query
from apps.common.constants import Lang

QUESTION = "Bu qancha turadi?"
HISTORY = [Turn("Doimiy propiska qanday rasmiylashtiriladi?", "NAMUNA propiska", "NAMUNA xulosa.")]


async def rewrite(rewriter: FakeQueryRewriter | None, history: list[Turn] = HISTORY) -> str:
    """Run the rewrite step with a generous timeout."""
    return await standalone_query(
        rewriter, question=QUESTION, language=Lang.UZ_LATN, history=history, timeout_s=5
    )


async def test_skipped_without_history() -> None:
    """A first question is retrieved as asked and costs no model call."""
    rewriter = FakeQueryRewriter("ignored")
    assert await rewrite(rewriter, history=[]) == QUESTION
    assert rewriter.prompts == []


async def test_skipped_when_off() -> None:
    """``QUERY_REWRITE=false`` wires no rewriter: the question is used."""
    assert await rewrite(None) == QUESTION


async def test_used_with_history() -> None:
    """With history the rewrite is used, built from the rewrite-v1 prompt."""
    rewriter = FakeQueryRewriter("Doimiy propiska uchun davlat boji qancha?\n")
    assert await rewrite(rewriter) == "Doimiy propiska uchun davlat boji qancha?"
    prompt = rewriter.prompts[0]
    assert prompt.version == REWRITE_PROMPT_VERSION
    assert "User: Doimiy propiska qanday rasmiylashtiriladi?" in prompt.user
    assert prompt.user.rstrip().endswith(QUESTION)
    assert "Uzbek (Latin script)" in prompt.system


@pytest.mark.parametrize("reply", [RuntimeError("Gemini down"), ""])
async def test_falls_back_on_error_or_empty_reply(reply: str | Exception) -> None:
    """A failing or empty rewrite never breaks the answer: the question is used."""
    assert await rewrite(FakeQueryRewriter(reply)) == QUESTION


async def test_falls_back_on_timeout() -> None:
    """A slow rewrite is cut off and the question is used."""

    class Slow(FakeQueryRewriter):
        """A rewriter slower than the budget."""

        async def rewrite(self, prompt: Prompt) -> str:
            """Sleep past the timeout."""
            await asyncio.sleep(1)
            return "too late"

    query = await standalone_query(
        Slow("x", usage=Usage()),
        question=QUESTION,
        language=Lang.UZ_LATN,
        history=HISTORY,
        timeout_s=0.01,
    )
    assert query == QUESTION


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ('"Propiska boji"', "Propiska boji"),
        ("\n\n  «Пошлина за прописку»  \nexplanation", "Пошлина за прописку"),
        ("x" * (REWRITE_MAX_CHARS + 50), "x" * REWRITE_MAX_CHARS),
        ("   \n", ""),
    ],
)
def test_clean_query(reply: str, expected: str) -> None:
    """Only the first line counts, quotes are stripped, length is capped."""
    assert clean_query(reply) == expected


def test_answer_prompts_stay_frozen() -> None:
    """The rewrite prompt is separate: v1–v3 keep their hashes (evaluation references them)."""
    assert load_template("v1").sha256.startswith("6ab5edfac386")
    assert load_template(REWRITE_PROMPT_VERSION).sha256 != load_template("v3").sha256
