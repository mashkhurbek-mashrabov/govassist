"""Tests for the district → region → none office lookup."""

import pytest

from apps.corpus.models import Document
from apps.geo.models import District
from apps.offices.locator import locate
from apps.offices.models import OfficeType
from conftest import make_office, namuna_document

pytestmark = pytest.mark.django_db


def _locate(doc: Document, district: District) -> dict[str, object] | None:
    """Locate for one document and a user in ``district``."""
    return locate([doc.id], district_id=district.id, region_id=district.region_id, lang="ru")


def test_district_match(
    passport_doc: Document, office_type: OfficeType, district: District
) -> None:
    """An office in the user's district wins, with localized labels and a maps URL."""
    office = make_office(office_type, district, latitude=41.3, longitude=69.2)
    result = _locate(passport_doc, district)
    assert result is not None
    assert result["match"] == "district"
    assert result["office_type"] == {"code": "public_service_center", "label": "Центр госуслуг"}
    card = result["office"]
    assert card["id"] == str(office.id)  # type: ignore[index]
    assert card["district"] == {"id": district.id, "name": "Тестовый район"}  # type: ignore[index]
    assert card["map_url"].endswith("query=41.3,69.2")  # type: ignore[index]
    assert card["working_hours"][0]["break"] == {"start": "13:00", "end": "14:00"}  # type: ignore[index]


def test_region_fallback(
    passport_doc: Document, office_type: OfficeType, district: District
) -> None:
    """No office in the district: another district of the same region."""
    neighbour = District.objects.create(
        id=9901202,
        region=district.region,
        name_uz_latn="Qoʻshni",
        name_uz_cyrl="Қўшни",
        name_ru="Соседний",
        name_en="Neighbour",
    )
    make_office(office_type, neighbour)
    result = _locate(passport_doc, district)
    assert result is not None
    assert result["match"] == "region"


def test_none_when_no_office(
    passport_doc: Document, office_type: OfficeType, district: District, other_district: District
) -> None:
    """Known office type, but only unapproved or far-away offices: match none."""
    make_office(office_type, district, status="pending")
    make_office(office_type, other_district)
    result = _locate(passport_doc, district)
    assert result == {
        "match": "none",
        "office_type": {"code": "public_service_center", "label": "Центр госуслуг"},
        "office": None,
    }


def test_no_mapping_means_no_office_event(office_type: OfficeType, district: District) -> None:
    """Laws and unconfirmed mappings give None."""
    law = namuna_document("NAMUNA qonun matni", kind="law", slug="law")
    assert _locate(law, district) is None
    assert locate([], district_id=None, region_id=None, lang="en") is None
