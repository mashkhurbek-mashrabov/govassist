"""Selectolax HTML parser for clean document text and link extraction."""

import re
import urllib.parse

from selectolax.lexbor import LexborHTMLParser, LexborNode

from apps.collector.fetchers import FetchResult
from apps.collector.parsers.base import ParsedPage

DROP_TAGS = frozenset(
    {"nav", "header", "footer", "script", "style", "noscript", "aside", "form"}
)
HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4"})
IGNORED_TABLE_TAGS = frozenset({"tr", "th", "td", "tbody", "thead", "tfoot"})
_COLLAPSE_NEWLINES = re.compile(r"\n{3,}")


def _render_heading(node: LexborNode) -> str:
    """Format heading with level hashes."""
    tag = node.tag or "h1"
    level = int(tag[1]) if len(tag) > 1 and tag[1].isdigit() else 1
    text = " ".join(node.text().split())
    return f"\n\n{'#' * level} {text}\n\n" if text else ""


def _render_paragraph(node: LexborNode) -> str:
    """Format paragraph separated by newlines."""
    text = " ".join(node.text().split())
    return f"\n\n{text}\n\n" if text else ""


def _render_list_item(node: LexborNode) -> str:
    """Format list item with hyphen bullet."""
    text = " ".join(node.text().split())
    return f"\n- {text}\n" if text else ""


def _render_table(node: LexborNode) -> str:
    """Format table rows joined by pipe delimiters."""
    rows: list[str] = []
    for tr in node.css("tr"):
        cells = [" ".join(c.text().split()) for c in tr.css("th, td")]
        if any(cells):
            rows.append(" | ".join(cells))
    return f"\n\n{'\n'.join(rows)}\n\n" if rows else ""


_TAG_HANDLERS = {
    "p": _render_paragraph,
    "li": _render_list_item,
    "table": _render_table,
}


def _render_node(node: LexborNode | None) -> str:
    """Recursively convert DOM node into Markdown-like formatted plain text.

    Args:
        node: The Lexbor node to render.

    Returns:
        Formatted text representation of the node and its subtree.
    """
    if node is None or node.tag is None:
        return ""
    tag = node.tag
    if tag == "-text":
        return node.text()
    if tag in HEADING_TAGS:
        return _render_heading(node)

    handler = _TAG_HANDLERS.get(tag)
    if handler is not None:
        return handler(node)

    pieces: list[str] = []
    if tag not in IGNORED_TABLE_TAGS:
        child = node.child
        while child is not None:
            pieces.append(_render_node(child))
            child = child.next
    return "".join(pieces)


def _extract_title(tree: LexborHTMLParser) -> str:
    """Extract document title prioritizing h1 over <title>.

    Args:
        tree: Parsed HTML tree.

    Returns:
        Extracted title or empty string.
    """
    h1 = tree.css_first("h1")
    if h1 is not None:
        text = " ".join(h1.text().split())
        if text:
            return text

    title_node = tree.css_first("title")
    if title_node is not None:
        text = " ".join(title_node.text().split())
        if text:
            return text

    return ""


def _extract_links(tree: LexborHTMLParser, base_url: str) -> list[str]:
    """Extract unique absolute HTTP/HTTPS links from anchor tags.

    Args:
        tree: Parsed HTML tree.
        base_url: Document base URL for relative resolution.

    Returns:
        List of absolute URLs stripped of fragment identifiers.
    """
    seen: set[str] = set()
    links: list[str] = []

    for a in tree.css("a[href]"):
        raw_href = a.attributes.get("href")
        if not raw_href or not isinstance(raw_href, str):
            continue
        href = raw_href.strip()
        if href.startswith(("javascript:", "mailto:", "tel:")):
            continue

        resolved = urllib.parse.urljoin(base_url, href)
        parsed = urllib.parse.urlsplit(resolved)
        if parsed.scheme not in {"http", "https"}:
            continue

        # Strip fragment
        clean_url = urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.query, "")
        )
        if clean_url not in seen:
            seen.add(clean_url)
            links.append(clean_url)

    return links


def parse_html(result: FetchResult) -> ParsedPage:
    """Parse HTML body with selectolax into a ParsedPage.

    Drops unneeded elements (nav, footer, script, etc.), formats headings,
    paragraphs, lists, and tables, extracts title and absolute links.

    Args:
        result: FetchResult with HTML bytes.

    Returns:
        ParsedPage instance.
    """
    html_text = result.body.decode("utf-8", errors="replace")
    tree = LexborHTMLParser(html_text)

    # Extract title before dropping headers if h1 is inside header
    title = _extract_title(tree)

    # Extract links before decomposing navigation
    links = _extract_links(tree, result.final_url)

    # Decompose unwanted sections
    for tag in DROP_TAGS:
        for node in tree.css(tag):
            node.decompose()

    # Re-evaluate title if empty
    if not title:
        title = _extract_title(tree)

    root = tree.body or tree.root
    rendered_raw = _render_node(root)
    clean_text = _COLLAPSE_NEWLINES.sub("\n\n", rendered_raw).strip()

    return ParsedPage(
        title=title,
        text=clean_text,
        links=links,
        published_at=None,
        section_label=None,
    )
