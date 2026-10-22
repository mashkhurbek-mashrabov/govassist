"""goldenpages.uz: company pages → one structured office; rubric pages → links only.

Read from the ``/uz/`` pages, whose names and addresses are Uzbek Latin. The phone is masked
on the page ("Show phone number"), so it is never stored and no reveal endpoint is called.
"""

import logging
import urllib.parse
from datetime import date
from typing import Any

from selectolax.lexbor import LexborHTMLParser, LexborNode

from apps.collector.constants import (
    DAY_LABELS,
    GOLDENPAGES_COMPANY,
    GOLDENPAGES_HOURS_ROW,
    GOLDENPAGES_RENEWED,
    GOLDENPAGES_RUBRIC,
    SCHEDULE_CELL_SELECTOR,
    SCHEDULE_DAY_CELL,
    SCHEDULE_HOURS_CELL,
    SCHEDULE_LUNCH_CELL,
    TIME_RANGE,
)
from apps.collector.extraction import ListedOffice
from apps.collector.fetchers import FetchResult
from apps.collector.parsers.base import ParsedPage
from apps.collector.parsers.directory import listed_office, listing_links, local_business
from apps.collector.parsers.html import clean, page_title, parse_html, tree_of
from apps.offices.hours import WorkingHours

logger = logging.getLogger(__name__)


def _time(hours: str, minutes: str) -> str:
    """``"9", "00"`` → ``"09:00"``."""
    return f"{int(hours):02d}:{minutes}"


def _range(text: str) -> tuple[str, str] | None:
    """``"09.00 - 18.00"`` → ``("09:00", "18:00")``, or None."""
    found = TIME_RANGE.search(text)
    if found is None:
        return None
    return _time(*found.group(1, 2)), _time(*found.group(3, 4))


def _day_row(row: LexborNode) -> tuple[str, dict[str, Any]] | None:
    """(day code, hours fields) of one schedule row, or None for a closed or unknown day."""
    cells = [clean(cell.text()) for cell in row.css(SCHEDULE_CELL_SELECTOR)]
    if len(cells) <= SCHEDULE_HOURS_CELL:
        return None
    day = DAY_LABELS.get(cells[SCHEDULE_DAY_CELL].rstrip(":").strip().lower())
    hours = _range(cells[SCHEDULE_HOURS_CELL])
    if day is None or hours is None:
        return None
    lunch = _range(cells[SCHEDULE_LUNCH_CELL]) if len(cells) > SCHEDULE_LUNCH_CELL else None
    pause = {"start": lunch[0], "end": lunch[1]} if lunch else None
    return day, {"open": hours[0], "close": hours[1], "break": pause}


def working_hours(tree: LexborHTMLParser) -> list[WorkingHours]:
    """The schedule table as contract §5 entries; consecutive identical days are merged.

    Args:
        tree: A company page.
    """
    groups: list[tuple[list[str], dict[str, Any]]] = []
    for row in tree.css(GOLDENPAGES_HOURS_ROW):
        parsed = _day_row(row)
        if parsed is None:
            continue
        day, fields = parsed
        if groups and groups[-1][1] == fields:
            groups[-1][0].append(day)
        else:
            groups.append(([day], fields))
    return [WorkingHours.model_validate({"days": days, **fields}) for days, fields in groups]


def _renewed(tree: LexborHTMLParser) -> date | None:
    """The page's "Yangilangan: dd.mm.yyyy" date, or None."""
    body = tree.body
    found = GOLDENPAGES_RENEWED.search(body.text() if body is not None else "")
    if found is None:
        return None
    day, month, year = (int(part) for part in found.groups())
    return date(year, month, day)


def _office(tree: LexborHTMLParser) -> ListedOffice | None:
    """The office of a company page (LocalBusiness JSON-LD + schedule table), or None."""
    business = local_business(tree)
    if business is None:
        return None
    return listed_office(business, business, hours=working_hours(tree), data_as_of=_renewed(tree))


def parse_goldenpages(result: FetchResult) -> ParsedPage:
    """Parse a goldenpages.uz page.

    - Company page: one structured office, no links (nearby companies are not followed).
      Without a LocalBusiness block it falls back to the generic text (the extractor runs).
    - Rubric page: no offices; links to its companies and its other pages.

    Args:
        result: The fetched page.
    """
    path = urllib.parse.urlsplit(result.final_url).path
    tree = tree_of(result)
    if GOLDENPAGES_COMPANY.match(path):
        office = _office(tree)
        if office is None:
            logger.warning("No structured office data", extra={"url": result.final_url})
            fallback = parse_html(result)
            return ParsedPage(title=fallback.title, text=fallback.text)
        return ParsedPage(title=office.name, text="", offices=[office])
    links = (
        listing_links(tree, result.final_url, GOLDENPAGES_COMPANY)
        if GOLDENPAGES_RUBRIC.match(path)
        else []
    )
    return ParsedPage(title=page_title(tree), text="", links=links, offices=[])
