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
    """Two runs give the same rows: 8 contract office types and 7 one-page sources."""
    call_command("seed")
    call_command("seed")
    assert set(OfficeType.objects.values_list("code", flat=True)) == CONTRACT_OFFICE_TYPES
    assert CrawlSource.objects.count() == 7
    assert set(CrawlSource.objects.values_list("max_pages", flat=True)) == {1}
    assert all(
        url.startswith(("https://my.gov.uz/uz/service/", "https://lex.uz/uz/docs/"))
        for url in CrawlSource.objects.values_list("start_url", flat=True)
    )
    assert "7 sample sources" in capsys.readouterr().out
