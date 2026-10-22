from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class ParsedPage:
    """Clean text of one page with ``#`` heading markers, plus its metadata and links."""

    title: str
    text: str
    links: list[str] = field(default_factory=list)
    published_at: date | None = None
    section_label: str | None = None
