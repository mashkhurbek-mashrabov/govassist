"""lex.uz acts: the act body lives in ``#divCont`` as ``.lx_elem`` blocks with semantic classes.

Metadata comes only from the page title, whose shape is ``[<N>-сон ]DD.MM.YYYY. <name>``;
nothing is guessed from the body.
"""

import re
from datetime import date, datetime

from selectolax.lexbor import LexborNode

from apps.collector.fetchers import FetchResult
from apps.collector.parsers.base import ParsedPage
from apps.collector.parsers.html import clean, links_of, page_title, tidy, tree_of

CONTENT_SELECTOR = "#divCont"
NOISE_SELECTOR = ".lx_elem2, .lx_elem3, .lx_no_select, .COMMENTLEXUZ, script, style"
ARTICLE_CLASS = "CLAUSE_DEFAULT"
HEADER_CLASS = "TEXT_HEADER_DEFAULT"
PART_LEVEL, CHAPTER_LEVEL, ARTICLE_LEVEL = 1, 2, 3
_PART = re.compile(r"\b(boʻlim|bo'lim|bo‘lim|бўлим|раздел|part)\b", re.IGNORECASE)
_TITLE = re.compile(r"^(?:(?P<number>\S+-сон)\s+)?(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*(?P<name>.+)$")
DATE_FORMAT = "%d.%m.%Y"


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
        return _marker(PART_LEVEL if _PART.search(text) else CHAPTER_LEVEL, text)
    return f"\n\n{text}\n\n"


def parse_title(raw: str) -> tuple[str, str | None, date | None]:
    """Split a lex.uz title into (name, act number, act date); unknown parts are None.

    Args:
        raw: The ``<title>`` text.
    """
    match = _TITLE.match(raw)
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
    for node in content.css(NOISE_SELECTOR):
        node.decompose()
    text = tidy("".join(_block(node) for node in content.css(".lx_elem")))
    return ParsedPage(
        title=name, text=text, links=links, published_at=act_date, section_label=number
    )
