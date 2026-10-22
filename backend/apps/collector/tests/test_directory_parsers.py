"""Tests for the goldenpages.uz and yellowpages.uz parsers (invented NAMUNA fixtures)."""

from datetime import date
from pathlib import Path

import pytest

from apps.collector.fetchers import FetchResult
from apps.collector.parsers import parse
from apps.collector.parsers.directory import (
    coordinate,
    district_from_name,
    same_listing,
    split_address,
)

FIXTURES = Path(__file__).parent / "fixtures"
GP = "https://www.goldenpages.uz"
YP = "https://www.yellowpages.uz"


def _page(url: str, fixture: str) -> FetchResult:
    """A 200 response for ``url`` with a saved fixture body."""
    body = (FIXTURES / fixture).read_bytes()
    return FetchResult(url=url, final_url=url, status=200, content_type="text/html", body=body)


def test_goldenpages_company_page_gives_one_structured_office() -> None:
    """Name, address, place, coordinates, merged hours with lunch and the 'updated' date."""
    page = parse(_page(f"{GP}/uz/company/?Id=1", "namuna_goldenpages_company.html"))
    assert page.links == []  # nearby companies are never followed
    assert page.offices is not None
    (office,) = page.offices
    assert office.name == "NAMUNA TUMANI DAVLAT XIZMATLARI MARKAZI (YAGONA DARCHA)"
    assert office.address == "Toshkent, Namuna tumani, Namuna ko'chasi, 1A"
    assert (office.region_name, office.district_name) == ("Toshkent", "Namuna tumani")
    assert (office.latitude, office.longitude) == (41.3, 69.2)
    assert office.phone is None  # masked on the page, never revealed
    assert office.data_as_of == date(2026, 4, 30)
    assert [h.model_dump(by_alias=True) for h in office.working_hours] == [
        {
            "days": ["mon", "tue", "wed"],
            "open": "09:00",
            "close": "18:00",
            "break": {"start": "13:00", "end": "14:00"},
        },
        {"days": ["sat"], "open": "09:00", "close": "13:00", "break": None},
    ]


def test_goldenpages_company_without_structured_data_falls_back_to_text() -> None:
    """No LocalBusiness block: offices is None, so the extractor reads the text."""
    body = b"<html><body><h1>NAMUNA idora</h1><p>Manzil: NAMUNA</p></body></html>"
    url = f"{GP}/uz/company/?Id=9"
    page = parse(
        FetchResult(url=url, final_url=url, status=200, content_type="text/html", body=body)
    )
    assert page.offices is None
    assert "Manzil: NAMUNA" in page.text


def test_goldenpages_rubric_page_links_companies_and_its_own_pages_only() -> None:
    """Listing pages yield no offices and only robots-safe company/pagination links."""
    page = parse(_page(f"{GP}/uz/rubrics/?Id=7", "namuna_goldenpages_rubric.html"))
    assert page.offices == []
    assert page.links == [
        f"{GP}/uz/company/?Id=1",
        f"{GP}/uz/company/?Id=2",
        f"{GP}/uz/rubrics/?Id=7&Page=2",
        f"{GP}/uz/rubrics/?Id=7&Page=3",
    ]


def test_other_goldenpages_pages_give_nothing() -> None:
    """Pages that are neither companies nor rubrics are not offices and have no links."""
    page = parse(_page(f"{GP}/uz/", "namuna_goldenpages_rubric.html"))
    assert (page.offices, page.links) == ([], [])


def test_yellowpages_company_page_reads_graph_geo_with_commas() -> None:
    """The LocalBusiness inside ``@graph``; ``"41,3271"`` coordinates; phone not stored."""
    page = parse(_page(f"{YP}/uz/korxona/namuna-bir", "namuna_yellowpages_company.html"))
    assert page.links == []
    assert page.offices is not None
    (office,) = page.offices
    assert office.name == "NAMUNA TUMANI DAVLAT XIZMATLARI MARKAZI"
    assert (office.region_name, office.district_name) == ("Toshkent", "Namuna tumani")
    assert office.address == "Toshkent, Namuna tumani, ko'chasi NAMUNA, 4 A"  # label dropped
    assert (office.latitude, office.longitude) == (41.3271, 69.2849)
    assert (office.phone, office.working_hours, office.data_as_of) == (None, [], None)


def test_yellowpages_company_without_structured_data_has_no_offices() -> None:
    """No LocalBusiness block: nothing is extracted from yellowpages text."""
    body = b"<html><head><title>NAMUNA</title></head><body>NAMUNA</body></html>"
    url = f"{YP}/uz/korxona/namuna"
    page = parse(
        FetchResult(url=url, final_url=url, status=200, content_type="text/html", body=body)
    )
    assert page.offices == []


def test_yellowpages_rubric_page_links() -> None:
    """Company pages and this listing's other pages; other cities and sections are not."""
    page = parse(_page(f"{YP}/uz/rubrika/namuna/toshkent", "namuna_yellowpages_rubric.html"))
    assert page.offices == []
    assert page.links == [
        f"{YP}/uz/korxona/namuna-bir",
        f"{YP}/uz/korxona/namuna-ikki",
        f"{YP}/uz/rubrika/namuna/toshkent?page=2",
    ]


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        (
            "100043, Toshkent, Chilonzor tumani, Bunyodkor ko'chasi, 7G",
            ("Toshkent", "Chilonzor tumani", "Toshkent, Chilonzor tumani, Bunyodkor ko'chasi, 7G"),
        ),
        (
            "140103, Samarqand viloyati, Samarqand, Amir Temur ko'chasi, 152",
            ("Samarqand viloyati", "", "Samarqand viloyati, Samarqand, Amir Temur ko'chasi, 152"),
        ),
        ("O'zbekiston, Namuna shahri, NAMUNA", ("", "Namuna shahri", "Namuna shahri, NAMUNA")),
        (
            "O'zbekiston, Toshkent viloyati, Toshkent, Yunusobod tumani, OSIYO, 4 A",
            ("Toshkent", "Yunusobod tumani", "Toshkent, Yunusobod tumani, OSIYO, 4 A"),
        ),
        ("", ("", "", "")),
    ],
)
def test_split_address(address: str, expected: tuple[str, str, str]) -> None:
    """Region is the part before the district part, else the first part."""
    place = split_address(address)
    assert (place.region_name, place.district_name, place.street) == expected


@pytest.mark.parametrize(
    ("name", "district"),
    [
        ("SAMARQAND TUMANI DAVLAT XIZMATLARI MARKAZI", "SAMARQAND tumani"),
        ("SAMARQAND SHAHAR DAVLAT XIZMATLARI MARKAZI", "SAMARQAND shahri"),
        ("ANDIJON VILOYATI ASAKA TUMAN IIB MIGRATSIYA BO'LIMI", "ASAKA tumani"),
        ("DAVLAT KADASTRLARI PALATASINING CHILONZOR TUMAN FILIALI", "CHILONZOR tumani"),
        ("BEKTEMIR TUMANINING PASPORT BO'LIMI", "BEKTEMIR tumani"),
        ("SAMARQAND VILOYATI DAVLAT SOLIQ BOSHQARMASI", ""),
    ],
)
def test_district_from_name(name: str, district: str) -> None:
    """The one word before TUMAN/SHAHAR is the district or city."""
    assert district_from_name(name) == district


@pytest.mark.parametrize(
    ("raw", "value"), [("41,32", 41.32), ("69.2", 69.2), ("", None), ("nan", None), (None, None)]
)
def test_coordinate(raw: object, value: float | None) -> None:
    """Comma or dot decimals; anything else is None."""
    assert coordinate(raw) == value


def test_same_listing_only_differs_by_page() -> None:
    """Another page of the same listing, not another listing."""
    url = f"{GP}/uz/rubrics/?Id=7"
    assert same_listing(url, f"{GP}/uz/rubrics/?Id=7&Page=2")
    assert not same_listing(url, f"{GP}/uz/rubrics/?Id=8&Page=2")
    assert not same_listing(url, f"{GP}/uz/rubrics/?Id=7")
    assert not same_listing(url, f"{GP}/en/rubrics/?Id=7&Page=2")
