"""PDF text via pdfplumber."""

import io
import urllib.parse
from pathlib import PurePosixPath

import pdfplumber

from apps.collector.constants import MAX_TITLE_CHARS
from apps.collector.fetchers import FetchResult
from apps.collector.parsers.base import ParsedPage


def parse_pdf(result: FetchResult) -> ParsedPage:
    """Join the text of every page with blank lines; title = first short line or file name.

    Args:
        result: The fetched PDF.
    """
    with pdfplumber.open(io.BytesIO(result.body)) as pdf:
        pages = [(page.extract_text() or "").strip() for page in pdf.pages]
    text = "\n\n".join(page for page in pages if page)
    first_line = text.split("\n", 1)[0].strip()
    file_name = PurePosixPath(urllib.parse.urlsplit(result.final_url).path).stem
    title = first_line if 0 < len(first_line) <= MAX_TITLE_CHARS else file_name
    return ParsedPage(title=title, text=text)
