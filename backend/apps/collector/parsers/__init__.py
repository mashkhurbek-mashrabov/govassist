"""Parsers: pick by content type, then by host."""

from collections.abc import Callable

from apps.collector.fetchers import FetchResult, host_of
from apps.collector.parsers.base import ParsedPage
from apps.collector.parsers.html import parse_html
from apps.collector.parsers.lexuz import parse_lexuz
from apps.collector.parsers.mygov import parse_mygov
from apps.collector.parsers.pdf import parse_pdf

__all__ = ["ParsedPage", "parse"]

HOST_PARSERS: dict[str, Callable[[FetchResult], ParsedPage]] = {
    "lex.uz": parse_lexuz,
    "my.gov.uz": parse_mygov,
}


def parse(result: FetchResult) -> ParsedPage:
    """Parse a fetched page with the parser for its type and host.

    Args:
        result: The fetched page.
    """
    if result.is_pdf:
        return parse_pdf(result)
    host = host_of(result.final_url).removeprefix("www.")
    return HOST_PARSERS.get(host, parse_html)(result)
