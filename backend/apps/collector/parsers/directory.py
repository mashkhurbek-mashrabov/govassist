"""Shared reading of business-directory pages (goldenpages.uz, yellowpages.uz).

Both sites publish a schema.org ``LocalBusiness`` block as JSON-LD. The office is read from
that structured data; the page text is never sent to the LLM when the block is present.
"""

import json
import math
import re
import urllib.parse
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from typing import Any

from selectolax.lexbor import LexborHTMLParser

from apps.collector.constants import (
    CITY_KINDS,
    CITY_LABEL,
    COUNTRY_NAMES,
    DISTRICT_LABEL,
    DISTRICT_PART,
    LD_JSON_SELECTOR,
    LOCAL_BUSINESS,
    NAME_DISTRICT,
    PAGE_PARAMS,
    POSTAL_CODE,
)
from apps.collector.extraction import ListedOffice
from apps.collector.parsers.html import clean, links_of
from apps.offices.hours import WorkingHours


def _nodes(data: Any) -> Iterator[dict[str, Any]]:
    """Every JSON object in a JSON-LD document (top level, lists and ``@graph``)."""
    if isinstance(data, dict):
        yield data
        for value in data.values():
            yield from _nodes(value)
    elif isinstance(data, list):
        for value in data:
            yield from _nodes(value)


def local_business(tree: LexborHTMLParser) -> dict[str, Any] | None:
    """The page's schema.org ``LocalBusiness`` JSON-LD object, or None.

    Invalid JSON-LD blocks are skipped: the page is third-party data.

    Args:
        tree: The parsed page.
    """
    for script in tree.css(LD_JSON_SELECTOR):
        try:
            data = json.loads(script.text())
        except ValueError:
            continue
        for node in _nodes(data):
            if node.get("@type") == LOCAL_BUSINESS:
                return node
    return None


@dataclass(frozen=True)
class Place:
    """Where an address says an office is.

    ``district_name`` is empty when the address names no district; ``street`` is the
    address without postal code and country.
    """

    region_name: str
    district_name: str
    street: str


def split_address(address: str) -> Place:
    """Split a directory address into region, district and street.

    ``"100043, Toshkent, Chilonzor tumani, Bunyodkor ko'chasi, 7G"`` → region ``Toshkent``,
    district ``Chilonzor tumani``. The region is the part just before the district part, or
    the first part when no part names a district.

    Args:
        address: The ``streetAddress`` as published.
    """
    parts = [clean(part) for part in address.split(",")]
    parts = [p for p in parts if p and not POSTAL_CODE.match(p) and p.lower() not in COUNTRY_NAMES]
    district_at = next((i for i, part in enumerate(parts) if DISTRICT_PART.search(part)), None)
    if district_at is None:
        return Place(parts[0] if parts else "", "", ", ".join(parts))
    region = parts[district_at - 1] if district_at > 0 else ""
    return Place(region, parts[district_at], ", ".join(parts))


def district_from_name(name: str) -> str:
    """The district an office name states (``"SAMARQAND TUMANI ..."`` → ``"SAMARQAND tumani"``).

    Args:
        name: The office name.

    Returns:
        ``"<place> tumani"`` or ``"<place> shahri"``, or ``""`` when the name states none.
    """
    found = NAME_DISTRICT.search(name)
    if found is None:
        return ""
    label = CITY_LABEL if found["kind"].lower() in CITY_KINDS else DISTRICT_LABEL
    return f"{found['place']} {label}"


def coordinate(value: Any) -> float | None:
    """A latitude/longitude from JSON-LD (``"41,32"`` or ``"41.32"``), or None.

    Args:
        value: The raw value.
    """
    try:
        number = float(str(value).replace(",", "."))
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def same_listing(url: str, link: str) -> bool:
    """True when ``link`` is another page (``?page=N``) of the listing at ``url``.

    Args:
        url: The listing page URL.
        link: A link found on it.
    """
    here, there = urllib.parse.urlsplit(url), urllib.parse.urlsplit(link)
    if (here.netloc, here.path) != (there.netloc, there.path):
        return False
    strip = {k: v for k, v in urllib.parse.parse_qsl(there.query) if k not in PAGE_PARAMS}
    keep = {k: v for k, v in urllib.parse.parse_qsl(here.query) if k not in PAGE_PARAMS}
    paged = any(k in PAGE_PARAMS for k, _ in urllib.parse.parse_qsl(there.query))
    return paged and strip == keep


def listing_links(tree: LexborHTMLParser, url: str, company: re.Pattern[str]) -> list[str]:
    """Links a listing page leads to: same-host company pages and its own further pages.

    Args:
        tree: The listing page.
        url: Its URL.
        company: Path pattern of the site's company pages.
    """
    host = urllib.parse.urlsplit(url).netloc
    keep = []
    for link in links_of(tree, url):
        parts = urllib.parse.urlsplit(link)
        if parts.netloc == host and (company.match(parts.path) or same_listing(url, link)):
            keep.append(link)
    return keep


def listed_office(
    business: dict[str, Any],
    geo: dict[str, Any],
    *,
    hours: list[WorkingHours] | None = None,
    data_as_of: date | None = None,
) -> ListedOffice | None:
    """An office from a LocalBusiness block, or None without a name or address.

    The phone is never stored: directory sites mask it on the page.

    Args:
        business: The LocalBusiness JSON-LD object.
        geo: The object holding ``latitude``/``longitude`` (the block or its ``geo``).
        hours: Working hours read from the page, if any.
        data_as_of: The directory's own "updated" date, if stated.
    """
    name = clean(str(business.get("name") or ""))
    street = clean(str((business.get("address") or {}).get("streetAddress") or ""))
    if not name or not street:
        return None
    place = split_address(street)
    return ListedOffice(
        name=name,
        address=place.street,
        region_name=place.region_name,
        district_name=place.district_name or district_from_name(name),
        phone=None,
        working_hours=hours or [],
        latitude=coordinate(geo.get("latitude")),
        longitude=coordinate(geo.get("longitude")),
        data_as_of=data_as_of,
    )
