"""lex.uz acts: the act body lives in ``#divCont`` as ``.lx_elem`` blocks with semantic classes.

Metadata comes only from the page title, whose shape is ``[<N>-сон ]DD.MM.YYYY. <name>``;
nothing is guessed from the body.
"""

from datetime import date, datetime

from selectolax.lexbor import LexborNode

from apps.collector.constants import (
    ARTICLE_CLASS,
    CONTENT_SELECTOR,
    DATE_FORMAT,
    HEADER_CLASS,
    LEXUZ_NOISE_SELECTOR,
    PART,
    TITLE,
)
from apps.collector.fetchers import FetchResult
from apps.collector.parsers.base import ParsedPage
from apps.collector.parsers.html import clean, links_of, page_title, tidy, tree_of

PART_LEVEL, CHAPTER_LEVEL, ARTICLE_LEVEL = 1, 2, 3


def _marker(level: int, text: str) -> str:
    """A heading marker line."""
    return f"\n\n{'#' * level} {text}\n\n"


def _block(node: LexborNode) -> str:
    """Render one ``.lx_elem`` block as a heading marker or a paragraph."""
    text = clean(node.text())
    if not text:
        return ""
    classes = (node.attributes.get("class") or "").split()
    if ARTICLE_CLASS in classes:
        return _marker(ARTICLE_LEVEL, text)
    if HEADER_CLASS in classes:
        return _marker(PART_LEVEL if PART.search(text) else CHAPTER_LEVEL, text)
    return f"\n\n{text}\n\n"


def parse_title(raw: str) -> tuple[str, str | None, date | None]:
    """Split a lex.uz title into (name, act number, act date); unknown parts are None.

    Args:
        raw: The ``<title>`` text.
    """
    match = TITLE.match(raw)
    if match is None:
        return raw, None, None
    act_date = datetime.strptime(match["date"], DATE_FORMAT).date()
    return match["name"].strip(), match["number"], act_date


def parse_lexuz(result: FetchResult) -> ParsedPage:
    """Parse a lex.uz act page into article-marked text.

    Args:
        result: The fetched page.
    """
    tree = tree_of(result)
    name, number, act_date = parse_title(page_title(tree))
    links = links_of(tree, result.final_url)
    content = tree.css_first(CONTENT_SELECTOR)
    if content is None:
        return ParsedPage(title=name, text="", links=links, section_label=number)
    for node in content.css(LEXUZ_NOISE_SELECTOR):
        node.decompose()
    text = tidy("".join(_block(node) for node in content.css(".lx_elem")))
    return ParsedPage(
        title=name, text=text, links=links, published_at=act_date, section_label=number
    )
