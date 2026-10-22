"""PII scrubber: runs before storage, embedding, Gemini calls and logging (plan §7)."""

import re

_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[EMAIL]"),
    (re.compile(r"\b\d{14}\b"), "[PINFL]"),
    (re.compile(r"\b[A-Z]{2}\s?\d{7}\b", re.IGNORECASE), "[PASSPORT]"),
    (
        re.compile(r"(?<![\w+])(\+?998[\s-]?)?\(?\d{2}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)"),
        "[PHONE]",
    ),
)
"""Order matters: emails and 14-digit PINFLs go first so the phone rule never eats them."""


def scrub(text: str) -> str:
    """Replace passport numbers, PINFLs, phones and emails with placeholders.

    Args:
        text: Raw user text.

    Returns:
        Text with ``[PASSPORT]``, ``[PINFL]``, ``[PHONE]`` and ``[EMAIL]`` placeholders.
    """
    for pattern, placeholder in _RULES:
        text = pattern.sub(placeholder, text)
    return text
