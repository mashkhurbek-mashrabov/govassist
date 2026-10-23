"""Standalone retrieval queries for follow-up questions (issue #34, contract v1.11).

Only retrieval uses the rewrite: the stored question and the answer prompt keep the user's
text. Any failure falls back to the question as asked.
"""

import asyncio
import logging
from collections.abc import Sequence

from apps.chat.constants import QUOTE_CHARS, REWRITE_MAX_CHARS, REWRITE_PROMPT_VERSION
from apps.chat.generator import QueryRewriter
from apps.chat.prompts import Turn, render_prompt
from apps.common.constants import Lang

logger = logging.getLogger(__name__)


def clean_query(reply: str) -> str:
    """The first non-empty line of the reply, without quotes, capped in length.

    Args:
        reply: The rewriter's raw reply.
    """
    line = next((line.strip() for line in reply.splitlines() if line.strip()), "")
    return line.strip(QUOTE_CHARS).strip()[:REWRITE_MAX_CHARS]


async def standalone_query(
    rewriter: QueryRewriter | None,
    *,
    question: str,
    language: Lang,
    history: Sequence[Turn],
    timeout_s: float,
) -> str:
    """Rewrite a follow-up into a self-contained query; skipped without history.

    Args:
        rewriter: The rewriter, or None when rewriting is off.
        question: The scrubbed question.
        language: The question's language.
        history: Earlier turns, oldest first (already scrubbed).
        timeout_s: Time allowed for the rewrite.

    Returns:
        The query to retrieve with: the rewrite, or ``question`` when skipped or failed.
    """
    if rewriter is None or not history:
        return question
    prompt = render_prompt(
        version=REWRITE_PROMPT_VERSION,
        language=language,
        question=question,
        context=[],
        history=history,
        office_type_label=None,
    )
    try:
        async with asyncio.timeout(timeout_s):
            reply = await rewriter.rewrite(prompt)
    except Exception:
        logger.warning("Query rewrite failed; retrieving with the question as asked", exc_info=True)
        return question
    return clean_query(reply) or question
