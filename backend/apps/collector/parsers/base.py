"""Base data structures for parsed web and file content."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ParsedPage:
    """Structured representation of a parsed web document or file."""

    title: str
    text: str
    links: list[str]  # Absolute URLs
    published_at: date | None
    section_label: str | None
