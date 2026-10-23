"""Tests for the seed command."""

import pytest
from django.core.management import call_command

from apps.collector.models import CrawlSource
from apps.offices.models import OfficeType

pytestmark = pytest.mark.django_db
CONTRACT_OFFICE_TYPES = {
    "public_service_center",
    "migration",
    "civil_registry",
    "notary",
    "tax",
    "cadastre",
    "khokimiyat",
    "other",
}


def test_seed_is_idempotent(capsys: pytest.CaptureFixture[str]) -> None:
    """Two runs give the same rows: 8 office types, 19 one-page sources, 15 directory sources."""
    call_command("seed")
    call_command("seed")
    assert set(OfficeType.objects.values_list("code", flat=True)) == CONTRACT_OFFICE_TYPES
    documents = CrawlSource.objects.filter(kind=CrawlSource.Kind.DOCUMENT)
    assert documents.count() == 19
    assert set(documents.values_list("max_pages", flat=True)) == {1}
    assert all(
        url.startswith(("https://my.gov.uz/uz/service/", "https://lex.uz/uz/docs/"))
        for url in documents.values_list("start_url", flat=True)
    )
    offices = CrawlSource.objects.filter(kind=CrawlSource.Kind.OFFICE)
    assert offices.count() == 15
    assert all(source.office_type_id and source.office_regions.exists() for source in offices)
    assert set(offices.values_list("publisher", flat=True)) == {"goldenpages.uz", "yellowpages.uz"}
    assert "19 sample sources, 15 directory sources" in capsys.readouterr().out
