"""Parser package for crawled content."""

import urllib.parse

from apps.collector.fetchers import FetchResult
from apps.collector.models import CrawlSource
from apps.collector.parsers.base import ParsedPage
from apps.collector.parsers.html import parse_html
from apps.collector.parsers.lexuz import parse_lexuz
from apps.collector.parsers.pdf import parse_pdf

__all__ = ["ParsedPage", "parse", "parse_html", "parse_lexuz", "parse_pdf"]


def parse(result: FetchResult, source: CrawlSource) -> ParsedPage:
    """Parse a fetched resource into a ParsedPage based on type and host.

    Dispatches:
      - PDF content -> parse_pdf
      - lex.uz URLs -> parse_lexuz
      - Default HTML -> parse_html

    Args:
        result: Fetched page result.
        source: CrawlSource configuration.

    Returns:
        ParsedPage instance.
    """
    if (
        result.content_type == "application/pdf"
        or result.url.lower().endswith(".pdf")
        or result.final_url.lower().endswith(".pdf")
    ):
        return parse_pdf(result)

    source_host = urllib.parse.urlsplit(source.start_url).netloc.lower()
    final_host = urllib.parse.urlsplit(result.final_url).netloc.lower()
    if "lex.uz" in source_host or "lex.uz" in final_host:
        return parse_lexuz(result)

    return parse_html(result)
