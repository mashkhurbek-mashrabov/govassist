"""PDF document parser using pdfplumber."""

import io
import urllib.parse
from pathlib import PurePosixPath

import pdfplumber

from apps.collector.fetchers import FetchResult
from apps.collector.parsers.base import ParsedPage

MAX_TITLE_LENGTH = 200


def parse_pdf(result: FetchResult) -> ParsedPage:
    """Extract plain text from PDF pages joined by double newlines.

    Args:
        result: FetchResult with PDF binary content.

    Returns:
        ParsedPage instance.
    """
    page_texts: list[str] = []
    with pdfplumber.open(io.BytesIO(result.body)) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted and extracted.strip():
                page_texts.append(extracted.strip())

    joined_text = "\n\n".join(page_texts)

    # Determine title from first line of text or file name
    first_line = joined_text.splitlines()[0].strip() if joined_text else ""
    if first_line and len(first_line) < MAX_TITLE_LENGTH:
        title = first_line
    else:
        path = urllib.parse.urlsplit(result.final_url).path
        name = PurePosixPath(path).stem
        title = name if name else "Document"

    return ParsedPage(
        title=title,
        text=joined_text,
        links=[],
        published_at=None,
        section_label=None,
    )
