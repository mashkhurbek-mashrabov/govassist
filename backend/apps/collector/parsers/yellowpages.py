"""yellowpages.uz: company pages → one structured office; rubric pages → links only.

The second directory, a cross-check for goldenpages.uz. Its addresses sometimes label
Tashkent city as "Toshkent viloyati", so the pipeline settles the region by the district.
The phone comes from the LocalBusiness ``telephone`` the page publishes; the page states no
working hours in structured form, so none are stored.
"""

import urllib.parse

from selectolax.lexbor import LexborHTMLParser

from apps.collector.constants import YELLOWPAGES_COMPANY, YELLOWPAGES_RUBRIC
from apps.collector.extraction import ListedOffice
from apps.collector.fetchers import FetchResult
from apps.collector.parsers.base import ParsedPage
from apps.collector.parsers.directory import (
    listed_office,
    listing_links,
    local_business,
    phone_from,
)
from apps.collector.parsers.html import page_title, tree_of


def _office(tree: LexborHTMLParser) -> ListedOffice | None:
    """The office of a company page (LocalBusiness JSON-LD in ``@graph``), or None."""
    business = local_business(tree)
    if business is None:
        return None
    phone = phone_from(str(business.get("telephone") or ""))
    return listed_office(business, business.get("geo") or {}, phone=phone)


def parse_yellowpages(result: FetchResult) -> ParsedPage:
    """Parse a yellowpages.uz page.

    - Company page: one structured office (none without a LocalBusiness block), no links.
    - Rubric page: no offices; links to its companies and its other pages.

    Args:
        result: The fetched page.
    """
    path = urllib.parse.urlsplit(result.final_url).path
    tree = tree_of(result)
    if YELLOWPAGES_COMPANY.match(path):
        office = _office(tree)
        return ParsedPage(
            title=office.name if office else page_title(tree),
            text="",
            offices=[office] if office else [],
        )
    links = (
        listing_links(tree, result.final_url, YELLOWPAGES_COMPANY)
        if YELLOWPAGES_RUBRIC.match(path)
        else []
    )
    return ParsedPage(title=page_title(tree), text="", links=links, offices=[])
