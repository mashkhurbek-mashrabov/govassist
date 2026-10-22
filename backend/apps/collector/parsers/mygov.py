"""my.gov.uz service pages: accordion sections (``.item`` + ``.accordionContent``)."""

from selectolax.lexbor import LexborNode

from apps.collector.constants import MYGOV_NOISE_SELECTOR, SECTION_SELECTOR, SERVICE_SELECTOR
from apps.collector.fetchers import FetchResult
from apps.collector.parsers.base import ParsedPage
from apps.collector.parsers.html import clean, links_of, page_title, render, tidy, tree_of


def _section(node: LexborNode) -> str:
    """An accordion title becomes a ``Title:`` line; its content is rendered as text.

    Titles are not heading markers, so a whole service page stays one coherent chunk.
    """
    classes = (node.attributes.get("class") or "").split()
    if "accordionContent" in classes:
        return render(node)
    title = node.css_first("span")
    text = clean(title.text() if title is not None else node.text())
    return f"\n\n{text}:\n\n" if text else ""


def parse_mygov(result: FetchResult) -> ParsedPage:
    """Parse a my.gov.uz service page: title, then fee, legal basis, time, documents, steps.

    Ratings, usage statistics and portal chrome are left out.

    Args:
        result: The fetched page.
    """
    tree = tree_of(result)
    links = links_of(tree, result.final_url)
    box = tree.css_first(SERVICE_SELECTOR)
    if box is not None:
        for node in box.css(f".accordionContent {MYGOV_NOISE_SELECTOR}"):
            node.decompose()
    heading = box.css_first("h1") if box is not None else None
    title = clean(heading.text()) if heading is not None else page_title(tree)
    sections = box.css(SECTION_SELECTOR) if box is not None else []
    return ParsedPage(title=title, text=tidy("".join(_section(n) for n in sections)), links=links)
