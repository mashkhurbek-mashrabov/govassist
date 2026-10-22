"""Generic HTML → text with ``#`` heading markers (selectolax)."""

import urllib.parse

from selectolax.lexbor import LexborHTMLParser, LexborNode

from apps.collector.constants import (
    BLOCK_TAGS,
    DROP_SELECTOR,
    HEADING_TAGS,
    MANY_NEWLINES,
    SKIPPED_SCHEMES,
    TEXT_NODE,
)
from apps.collector.fetchers import FetchResult
from apps.collector.parsers.base import ParsedPage


def clean(text: str) -> str:
    """Collapse whitespace to single spaces."""
    return " ".join(text.split())


def _table(node: LexborNode) -> str:
    """Flatten a table to ``cell | cell`` rows."""
    rows = [" | ".join(clean(cell.text()) for cell in row.css("th, td")) for row in node.css("tr")]
    return "\n".join(row for row in rows if row.strip(" |"))


def render(node: LexborNode) -> str:
    """Render a subtree: headings as ``#`` lines, blocks and list items as paragraphs.

    Args:
        node: The subtree root.
    """
    tag = node.tag
    if tag == TEXT_NODE:
        return node.text(deep=False)
    if tag in HEADING_TAGS:
        text = clean(node.text())
        return f"\n\n{'#' * int(tag[1])} {text}\n\n" if text else ""
    if tag == "table":
        return f"\n\n{_table(node)}\n\n"
    if tag == "li":
        text = clean(node.text())
        return f"\n\n- {text}\n\n" if text else ""
    if tag == "br":
        return "\n"
    inner = "".join(render(child) for child in node.iter(include_text=True))
    return f"\n\n{inner}\n\n" if tag in BLOCK_TAGS else inner


def tidy(text: str) -> str:
    """Strip each line, collapse runs of blank lines and trim."""
    lines = (" ".join(line.split()) for line in text.splitlines())
    return MANY_NEWLINES.sub("\n\n", "\n".join(lines)).strip()


def links_of(tree: LexborHTMLParser, base_url: str) -> list[str]:
    """Unique absolute http(s) links, without fragments, in page order.

    Args:
        tree: The parsed page.
        base_url: URL to resolve relative links against.
    """
    seen: dict[str, None] = {}
    for anchor in tree.css("a[href]"):
        href = (anchor.attributes.get("href") or "").strip()
        if not href or href.startswith(SKIPPED_SCHEMES):
            continue
        url, _ = urllib.parse.urldefrag(urllib.parse.urljoin(base_url, href))
        if urllib.parse.urlsplit(url).scheme in {"http", "https"}:
            seen.setdefault(url, None)
    return list(seen)


def page_title(tree: LexborHTMLParser) -> str:
    """The ``<title>`` text, else the first ``<h1>``."""
    for selector in ("title", "h1"):
        node = tree.css_first(selector)
        if node is not None and clean(node.text()):
            return clean(node.text())
    return ""


def tree_of(result: FetchResult) -> LexborHTMLParser:
    """Parse the response body as HTML (UTF-8, invalid bytes replaced)."""
    return LexborHTMLParser(result.body.decode("utf-8", errors="replace"))


def parse_html(result: FetchResult) -> ParsedPage:
    """Parse any HTML page: drop chrome (nav, header, footer, scripts, forms) and render.

    Args:
        result: The fetched page.
    """
    tree = tree_of(result)
    title, links = page_title(tree), links_of(tree, result.final_url)
    for node in tree.css(DROP_SELECTOR):
        node.decompose()
    body = tree.body
    text = tidy(render(body)) if body is not None else ""
    return ParsedPage(title=title, text=text, links=links)
