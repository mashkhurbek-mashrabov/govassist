"""OfficePipeline with structured directory offices: scope, ambiguity, dedup, dates."""

from datetime import date, datetime
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.collector.constants import DIRECTORY_FOLLOW
from apps.collector.crawler import Crawler
from apps.collector.extraction import FakeOfficeExtractor, ListedOffice
from apps.collector.fetchers import HostRateLimiter
from apps.collector.models import CrawlJob, CrawlSource
from apps.collector.parsers import ParsedPage
from apps.collector.pipelines import OfficePipeline, distance_m, find_regions
from apps.collector.tests.test_crawler import FakeFetcher, FakeRobots
from apps.geo.models import District, Region
from apps.offices.models import Office, OfficeType

pytestmark = pytest.mark.django_db
URL = "https://www.goldenpages.uz/uz/company/?Id=1"
NOW = datetime(2026, 10, 22, 9, 0, tzinfo=timezone.get_current_timezone())


@pytest.fixture
def places() -> dict[str, District]:
    """Test-only city and region that share the name "Toshkent", plus a third region."""
    city = Region.objects.create(id=9726, name_uz_latn="Toshkent shahri", name_ru="г. Ташкент")
    oblast = Region.objects.create(id=9727, name_uz_latn="Toshkent viloyati", name_ru="Ташкентская")
    other = Region.objects.create(id=9718, name_uz_latn="Namuna viloyati", name_ru="Намуна")
    return {
        "city": District.objects.create(id=9726201, region=city, name_uz_latn="Namuna tumani"),
        "oblast": District.objects.create(id=9727201, region=oblast, name_uz_latn="Qishloq tumani"),
        "other": District.objects.create(id=9718201, region=other, name_uz_latn="Chekka tumani"),
    }


@pytest.fixture
def office_type() -> OfficeType:
    """A NAMUNA office type."""
    return OfficeType.objects.create(code="tax", name_uz_latn="NAMUNA soliq")


def _source(office_type: OfficeType, regions: list[Region], pattern: str = "") -> CrawlSource:
    """An office source scoped to ``regions``."""
    source = CrawlSource.objects.create(
        name="NAMUNA",
        start_url="https://www.goldenpages.uz/uz/rubrics/?Id=1",
        kind=CrawlSource.Kind.OFFICE,
        office_type=office_type,
        publisher="goldenpages.uz",
        office_name_pattern=pattern,
    )
    source.office_regions.set(regions)
    return source


def _office(**extra: object) -> ListedOffice:
    """A NAMUNA listed office in the city's district."""
    data: dict[str, object] = {
        "name": "NAMUNA TUMANI SOLIQ INSPEKSIYASI",
        "address": "Toshkent, Namuna tumani, NAMUNA ko'chasi, 1",
        "region_name": "Toshkent",
        "district_name": "Namuna tumani",
        "latitude": 41.3,
        "longitude": 69.2,
        "data_as_of": date(2026, 4, 30),
    }
    return ListedOffice.model_validate(data | extra)


def _run(source: CrawlSource, *offices: ListedOffice) -> FakeOfficeExtractor:
    """Process one page with these structured offices; return the (unused) extractor."""
    extractor = FakeOfficeExtractor()
    page = ParsedPage(title="NAMUNA", text="", offices=list(offices))
    OfficePipeline(extractor).process(source, page, url=URL, fetched_at=NOW)
    return extractor


def test_structured_offices_skip_the_extractor_and_keep_the_page_date(
    office_type: OfficeType, places: dict[str, District]
) -> None:
    """Listed offices are stored pending as they are; data_as_of is the page's own date."""
    extractor = _run(_source(office_type, [places["city"].region]), _office())
    assert extractor.texts == []
    office = Office.objects.get()
    assert (office.status, office.district, office.region) == (
        "pending",
        places["city"],
        places["city"].region,
    )
    assert (office.data_as_of, office.needs_review, office.phone) == (
        date(2026, 4, 30),
        False,
        None,
    )


def test_ambiguous_toshkent_is_settled_by_the_district(
    office_type: OfficeType, places: dict[str, District]
) -> None:
    """The name Toshkent fits the city and the region; only the city has this district."""
    source = _source(office_type, [])
    _run(source, _office(), _office(name="NAMUNA QISHLOQ", district_name="Qishloq tumani"))
    assert dict(Office.objects.values_list("name", "region_id")) == {
        "NAMUNA TUMANI SOLIQ INSPEKSIYASI": 9726,
        "NAMUNA QISHLOQ": 9727,
    }


def test_mislabelled_region_is_settled_by_the_district(
    office_type: OfficeType, places: dict[str, District]
) -> None:
    """A city address labelled "Toshkent viloyati, Toshkent" resolves by its district.

    yellowpages does this; the part before the district ("Toshkent") plus the district decide.
    """
    _run(_source(office_type, [places["city"].region]), _office(region_name="Toshkent"))
    assert Office.objects.get().region_id == 9726


def test_out_of_scope_and_unmatched_offices_are_skipped(
    office_type: OfficeType, places: dict[str, District]
) -> None:
    """Other regions, other names and unknown districts are never stored."""
    source = _source(office_type, [places["city"].region], pattern="soliq")
    _run(
        source,
        _office(
            name="NAMUNA VILOYAT SOLIQ",
            region_name="Namuna viloyati",
            district_name="Chekka tumani",
        ),
        _office(name="NAMUNA BOSHQA IDORA", address="NAMUNA 2"),
        _office(name="NAMUNA YO'Q SOLIQ", district_name="Mavjud emas tumani", address="NAMUNA 3"),
        _office(name="NAMUNA SOLIQ, nomsiz joy", region_name="", address="NAMUNA 4"),
    )
    assert list(Office.objects.values_list("name", flat=True)) == ["NAMUNA SOLIQ, nomsiz joy"]


def test_duplicates_by_address_name_or_location_are_skipped(
    office_type: OfficeType, places: dict[str, District]
) -> None:
    """A second directory listing the same office (same spot, name or address) adds nothing."""
    source = _source(office_type, [places["city"].region])
    _run(source, _office())
    _run(
        source,
        _office(
            name="NAMUNA IKKINCHI NOM", address="Namuna tumani, boshqa yozuv", latitude=41.3005
        ),
        _office(address="boshqa manzil", latitude=None, longitude=None),
        _office(name="NAMUNA YANGI", address="NAMUNA 9", latitude=41.31, longitude=69.21),
    )
    assert sorted(Office.objects.values_list("name", flat=True)) == [
        "NAMUNA TUMANI SOLIQ INSPEKSIYASI",
        "NAMUNA YANGI",
    ]


def test_find_regions_full_name_beats_the_shared_short_name(places: dict[str, District]) -> None:
    """A full name is one region; the shared short name is both; unknown names are none."""
    assert [r.id for r in find_regions("Toshkent viloyati")] == [9727]
    assert sorted(r.id for r in find_regions("Toshkent")) == [9726, 9727]
    assert find_regions("Mavjud emas") == []


def test_distance_m() -> None:
    """About 55 m per 0.0005° of latitude; zero for the same point."""
    assert distance_m((41.3, 69.2), (41.3, 69.2)) == 0
    assert 50 < distance_m((41.3, 69.2), (41.3005, 69.2)) < 60


def test_invalid_name_pattern_is_rejected(office_type: OfficeType) -> None:
    """The admin cannot save a source whose name pattern is not a regex."""
    source = CrawlSource(
        name="NAMUNA",
        start_url=URL,
        kind=CrawlSource.Kind.OFFICE,
        office_type=office_type,
        publisher="namuna",
        office_name_pattern="(",
    )
    with pytest.raises(ValidationError, match="office_name_pattern"):
        source.clean()


def test_crawl_of_a_rubric_stores_its_companies_pending(
    office_type: OfficeType, places: dict[str, District]
) -> None:
    """Rubric → company pages → one pending office; listings never reach the extractor."""
    fixtures = Path(__file__).parent / "fixtures"
    rubric = (fixtures / "namuna_goldenpages_rubric.html").read_text(encoding="utf-8")
    company = (fixtures / "namuna_goldenpages_company.html").read_text(encoding="utf-8")
    start = "https://www.goldenpages.uz/uz/rubrics/?Id=7"
    site = {
        start: rubric,
        "https://www.goldenpages.uz/uz/company/?Id=1": company,
        "https://www.goldenpages.uz/uz/company/?Id=2": company,  # listed twice: one office
    }
    source = _source(office_type, [places["city"].region])
    source.start_url, source.max_pages = start, 20
    source.allowed_url_pattern = DIRECTORY_FOLLOW["goldenpages.uz"]
    source.save()
    extractor = FakeOfficeExtractor()
    crawler = Crawler(
        fetcher=FakeFetcher(site),
        pipeline=OfficePipeline(extractor),
        robots=FakeRobots(),  # type: ignore[arg-type]
        limiter=HostRateLimiter(1000, sleep=lambda s: None),
    )
    job = crawler.run(CrawlJob.objects.create(source=source))
    assert job.status == CrawlJob.Status.DONE
    assert (job.pages_fetched, job.pages_skipped) == (3, 2)  # pages 2 and 3 are 404
    office = Office.objects.get()
    assert (office.status, office.district, office.source_url) == (
        "pending",
        places["city"],
        "https://www.goldenpages.uz/uz/company/?Id=1",
    )
    assert extractor.texts == []
