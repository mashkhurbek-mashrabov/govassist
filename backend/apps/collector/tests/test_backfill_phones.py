"""Phones backfilled from saved pages only (no requests)."""

from pathlib import Path

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.collector.models import CrawlJob, CrawlSource, RawPage
from apps.geo.models import District
from apps.offices.models import Office, OfficeType
from conftest import make_office

pytestmark = pytest.mark.django_db
FIXTURE = Path(__file__).parent / "fixtures" / "namuna_goldenpages_company.html"
SAVED = "https://www.goldenpages.uz/uz/company/?Id=1"
NOT_SAVED = "https://www.goldenpages.uz/uz/company/?Id=2"


def _office(office_type: OfficeType, district: District, source: CrawlSource, url: str) -> Office:
    """A goldenpages office without a phone, listed at ``url``."""
    return make_office(
        office_type, district, source=source, source_url=url, phone=None, name=f"NAMUNA {url[-1]}"
    )


def test_phones_come_from_the_saved_page(
    office_type: OfficeType, district: District, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Dry run counts; the real run fills from the saved FAQ JSON-LD; unsaved pages are reported."""
    source = CrawlSource.objects.create(
        name="NAMUNA gp",
        start_url=SAVED,
        publisher="goldenpages.uz",
        kind="office",
        office_type=office_type,
    )
    saved = tmp_path / "page.html"
    saved.write_bytes(FIXTURE.read_bytes())
    RawPage.objects.create(
        job=CrawlJob.objects.create(source=source),
        url=SAVED,
        http_status=200,
        content_type="text/html",
        content_hash="0" * 64,
        raw_path=str(saved),
        fetched_at=timezone.now(),
    )
    with_page = _office(office_type, district, source, SAVED)
    _office(office_type, district, source, NOT_SAVED)

    call_command("backfill_phones", "--publisher", "goldenpages.uz", "--dry-run")
    with_page.refresh_from_db()
    assert with_page.phone is None
    call_command("backfill_phones", "--publisher", "goldenpages.uz")
    phones = dict(Office.objects.values_list("source_url", "phone"))
    assert phones == {SAVED: "+998000000000", NOT_SAVED: None}
    out = capsys.readouterr().out
    assert "Would fill 1 of 2 offices" in out
    assert "Filled 1 of 2 offices; 0 pages state no phone; 1 have no saved page." in out
