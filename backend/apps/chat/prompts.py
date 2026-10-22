"""Versioned prompt loading, rendering and hashing (plan §11).

``PROMPT_VERSION`` and the template's sha256 are stored on every answer.
"""

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from apps.common.i18n import Lang

PROMPTS_DIR = Path(__file__).parent / "prompts"
USER_MARKER = "=== USER ==="
NONE = "(none)"
LANGUAGE_NAMES = {
    Lang.UZ_LATN: "Uzbek (Latin script)",
    Lang.UZ_CYRL: "Uzbek (Cyrillic script)",
    Lang.RU: "Russian",
    Lang.EN: "English",
}


@dataclass(frozen=True)
class ContextBlock:
    """One retrieved chunk as the model sees it."""

    label: str
    title: str
    publisher: str
    section: str | None
    published_at: str | None
    text: str


@dataclass(frozen=True)
class Turn:
    """One earlier exchange: the user's (scrubbed) text and the answer's title/summary."""

    question: str
    answer_title: str
    answer_summary: str


@dataclass(frozen=True)
class Prompt:
    """A rendered prompt: system rules, user content and the template identity."""

    system: str
    user: str
    version: str
    sha256: str


@dataclass(frozen=True)
class _Template:
    """A loaded template split into its system and user parts."""

    system: str
    user: str
    sha256: str


@cache
def load_template(version: str) -> _Template:
    """Load and hash ``prompts/<version>.md``.

    Args:
        version: Prompt version, e.g. ``v1``.

    Raises:
        FileNotFoundError: When the version does not exist.
    """
    raw = (PROMPTS_DIR / f"{version}.md").read_text(encoding="utf-8")
    system, user = raw.split(USER_MARKER, maxsplit=1)
    return _Template(system.strip(), user.strip(), hashlib.sha256(raw.encode()).hexdigest())


def _context(blocks: Sequence[ContextBlock]) -> str:
    """Render ``[S1] title — publisher — section — date`` blocks."""
    rendered = []
    for block in blocks:
        meta = " — ".join(
            part
            for part in (block.title, block.publisher, block.section, block.published_at)
            if part
        )
        rendered.append(f"[{block.label}] {meta}\n{block.text}\n---")
    return "\n".join(rendered) or NONE


def _history(turns: Sequence[Turn]) -> str:
    """Render the last turns as ``User: … / Assistant: title — summary``."""
    lines = [f"User: {t.question}\nAssistant: {t.answer_title} — {t.answer_summary}" for t in turns]
    return "\n".join(lines) or NONE


def render_prompt(
    *,
    version: str,
    language: Lang,
    question: str,
    context: Sequence[ContextBlock],
    history: Sequence[Turn],
    office_type_label: str | None,
) -> Prompt:
    """Fill the template for one question.

    Args:
        version: Prompt version (``PROMPT_VERSION``).
        language: Detected language of the question.
        question: The scrubbed question.
        context: Retrieved chunks labelled S1..Sn.
        history: Earlier turns, oldest first.
        office_type_label: Label of the matched office type, if any.

    Returns:
        The rendered prompt.
    """
    template = load_template(version)
    # v1 uses office_reference (English scaffolding, kept for reproducibility); v2 uses only
    # the label so nothing English can leak into the answer.
    office_reference = (
        f'"the {office_type_label} shown below"'
        if office_type_label
        else '"the office shown below"'
    )
    system = template.system.format(
        language=LANGUAGE_NAMES[language],
        language_code=language.value,
        office_reference=office_reference,
        office_label=office_type_label or NONE,
    )
    user = template.user.format(
        context=_context(context),
        office=office_type_label or NONE,
        history=_history(history),
        question=question,
    )
    return Prompt(system=system, user=user, version=version, sha256=template.sha256)
