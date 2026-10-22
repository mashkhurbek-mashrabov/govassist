"""PII scrubber: runs before storage, embedding, Gemini calls and logging (plan §7)."""

from apps.common.constants import RULES


def scrub(text: str) -> str:
    """Replace passport numbers, PINFLs, phones and emails with placeholders.

    Args:
        text: Raw user text.

    Returns:
        Text with ``[PASSPORT]``, ``[PINFL]``, ``[PHONE]`` and ``[EMAIL]`` placeholders.
    """
    for pattern, placeholder in RULES:
        text = pattern.sub(placeholder, text)
    return text
