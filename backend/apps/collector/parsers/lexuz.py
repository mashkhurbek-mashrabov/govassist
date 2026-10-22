"""Specialized parser for lex.uz acts and legal documents."""

import re
from datetime import date

from apps.collector.fetchers import FetchResult
from apps.collector.parsers.base import ParsedPage
from apps.collector.parsers.html import parse_html

_MODDA_RE = re.compile(
    r"^(?:#{1,6}\s*)?(?:(\d+)-modda|Статья\s*(\d+)|Article\s*(\d+))(?:\.|\:|\b)",
    re.IGNORECASE,
)
_BOB_RE = re.compile(
    r"^(?:#{1,6}\s*)?(?:(\d+)-bob|Глава\s*(\d+)|Chapter\s*(\d+)|([IVXLCDM]+)\s+bob)(?:\.|\:|\b)",
    re.IGNORECASE,
)

_ACT_NUMBER_RE = re.compile(
    r"\b((?:O[ʻʼ'`]RQ|ЎРҚ|PQ|ПҚ|PF|ПФ|УП|VMQ|ВМҚ)[-–—\s]*\d+(?:-[IVXLCDM]+)?|\d+-сон(?:ли)?|№\s*[\dA-Za-zА-Яа-я\-_/]+)\b",
    re.IGNORECASE,
)

_UZ_DATE_RE = re.compile(
    r"\b(\d{4})-yil\s+(\d{1,2})-(yanvar|fevral|mart|aprel|may|iyun|iyul|avgust|sentabr|sentyabr|oktabr|oktyabr|noyabr|dekabr)\b",
    re.IGNORECASE,
)
_RU_DATE_RE = re.compile(
    r"\b(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})\s*(?:года|г\.)?\b",
    re.IGNORECASE,
)
_DOT_DATE_RE = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")

_MONTH_MAP = {
    "yanvar": 1,
    "fevral": 2,
    "mart": 3,
    "aprel": 4,
    "may": 5,
    "iyun": 6,
    "iyul": 7,
    "avgust": 8,
    "sentabr": 9,
    "sentyabr": 9,
    "oktabr": 10,
    "oktyabr": 10,
    "noyabr": 11,
    "dekabr": 12,
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


def _extract_act_number(text: str) -> str | None:
    """Extract official act identifier without guessing.

    Args:
        text: Page body or heading text.

    Returns:
        Extracted act number string or None.
    """
    match = _ACT_NUMBER_RE.search(text)
    return match.group(1).strip() if match else None


def _extract_date(text: str) -> date | None:
    """Extract adoption or publication date without guessing.

    Args:
        text: Text containing potential date mentions.

    Returns:
        date instance if matched and valid, else None.
    """
    uz_match = _UZ_DATE_RE.search(text)
    if uz_match:
        year = int(uz_match.group(1))
        day = int(uz_match.group(2))
        month = _MONTH_MAP.get(uz_match.group(3).lower(), 1)
        try:
            return date(year, month, day)
        except ValueError:
            pass

    ru_match = _RU_DATE_RE.search(text)
    if ru_match:
        day = int(ru_match.group(1))
        month = _MONTH_MAP.get(ru_match.group(2).lower(), 1)
        year = int(ru_match.group(3))
        try:
            return date(year, month, day)
        except ValueError:
            pass

    dot_match = _DOT_DATE_RE.search(text)
    if dot_match:
        day = int(dot_match.group(1))
        month = int(dot_match.group(2))
        year = int(dot_match.group(3))
        try:
            return date(year, month, day)
        except ValueError:
            pass

    return None


def _format_lex_markers(text: str) -> str:
    """Format article lines as level-3 (###) and chapter lines as level-2 (##).

    Args:
        text: Extracted plain text.

    Returns:
        Text with proper Markdown headings for articles and chapters.
    """
    formatted_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if _MODDA_RE.match(stripped):
            clean_line = re.sub(r"^#{1,6}\s*", "", stripped)
            formatted_lines.append(f"### {clean_line}")
        elif _BOB_RE.match(stripped):
            clean_line = re.sub(r"^#{1,6}\s*", "", stripped)
            formatted_lines.append(f"## {clean_line}")
        else:
            formatted_lines.append(line)
    return "\n".join(formatted_lines)


def parse_lexuz(result: FetchResult) -> ParsedPage:
    """Parse lex.uz page into structured ParsedPage with legal markers.

    Extracts:
      - Articles formatted with ### prefix
      - Chapters formatted with ## prefix
      - Act title, act number (section_label), publication date

    Args:
        result: FetchResult containing lex.uz HTML.

    Returns:
        ParsedPage instance.
    """
    base_page = parse_html(result)
    formatted_text = _format_lex_markers(base_page.text)

    act_number = _extract_act_number(formatted_text)
    pub_date = _extract_date(formatted_text)

    return ParsedPage(
        title=base_page.title,
        text=formatted_text,
        links=base_page.links,
        published_at=pub_date,
        section_label=act_number,
    )
