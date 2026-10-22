"""Tests for office approval and rejection services."""

from datetime import date

import pytest

from apps.common.models import ReviewStatus
from apps.geo.models import District, Region
from apps.offices.models import Office, OfficeType
from apps.offices.services import approve_offices, reject_offices


@pytest.mark.django_db
def test_approve_offices(region: Region, district: District) -> None:
    """Verifies approve_offices updates office status to APPROVED."""
    office_type = OfficeType.objects.create(
        code="public_service_center",
        name_uz_latn="Davlat xizmatlari markazi",
        name_uz_cyrl="Давлат хизматлари маркази",
        name_ru="Центр государственных услуг",
        name_en="Public Service Center",
    )
    office = Office.objects.create(
        office_type=office_type,
        name="NAMUNA Office",
        address="Test koʻchasi 1",
        district=district,
        region=region,
        data_as_of=date.today(),
        status=ReviewStatus.PENDING,
        source_url="https://example.uz/offices",
    )

    count = approve_offices(Office.objects.filter(id=office.id))
    assert count == 1
    office.refresh_from_db()
    assert office.status == ReviewStatus.APPROVED


@pytest.mark.django_db
def test_reject_offices(region: Region, district: District) -> None:
    """Verifies reject_offices updates office status to REJECTED."""
    office_type = OfficeType.objects.create(
        code="notary",
        name_uz_latn="Notarius",
        name_uz_cyrl="Нотариус",
        name_ru="Нотариус",
        name_en="Notary",
    )
    office = Office.objects.create(
        office_type=office_type,
        name="NAMUNA Notary",
        address="Test koʻchasi 2",
        district=district,
        region=region,
        data_as_of=date.today(),
        status=ReviewStatus.PENDING,
        source_url="https://example.uz/notary",
    )

    count = reject_offices(Office.objects.filter(id=office.id))
    assert count == 1
    office.refresh_from_db()
    assert office.status == ReviewStatus.REJECTED


@pytest.mark.django_db
def test_empty_querysets() -> None:
    """Verifies empty office querysets return 0."""
    empty_qs = Office.objects.none()
    assert approve_offices(empty_qs) == 0
    assert reject_offices(empty_qs) == 0
