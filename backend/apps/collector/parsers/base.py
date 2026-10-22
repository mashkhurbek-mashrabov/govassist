from dataclasses import dataclass, field
from datetime import date

from apps.collector.extraction import ListedOffice


@dataclass(frozen=True)
class ParsedPage:
    """Clean text of one page with ``#`` heading markers, plus its metadata and links.

    ``offices`` is set by directory parsers that read structured data: a list (possibly
    empty, e.g. a listing page) means "use these"; None means "no structure, extract from
    the text" (the Gemini fallback).
    """

    title: str
    text: str
    links: list[str] = field(default_factory=list)
    published_at: date | None = None
    section_label: str | None = None
    offices: list[ListedOffice] | None = None
