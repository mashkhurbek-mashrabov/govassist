"""Tests for the geo endpoints and SOATO seeding."""

import pytest
from rest_framework.test import APIClient

from apps.geo.models import District, Region
from apps.geo.services import seed_geo

pytestmark = pytest.mark.django_db


def test_regions_localized(api: APIClient, district: District) -> None:
    """Regions list uses ?lang=."""
    assert api.get("/api/v1/geo/regions?lang=uz-Cyrl").json() == [
        {"id": district.region_id, "name": "Тест вилояти"}
    ]


def test_districts_of_region(api: APIClient, district: District, other_district: District) -> None:
    """Only the region's districts are listed."""
    body = api.get(f"/api/v1/geo/regions/{district.region_id}/districts?lang=en").json()
    assert body == [{"id": district.id, "name": "Test district"}]


def test_seed_geo_loads_official_fixture() -> None:
    """The SOATO fixture seeds all regions and districts, idempotently."""
    assert seed_geo() == (14, 206)
    assert seed_geo() == (14, 206)
    tashkent = Region.objects.get(id=1726)
    assert tashkent.name_uz_latn == "Toshkent shahri"
    assert tashkent.name_en == "Toshkent shahri"
    assert District.objects.filter(region=tashkent).count() == 12
    assert District.objects.get(id=1727401).kind == District.Kind.CITY


def test_name_for_falls_back_to_latin(region: Region) -> None:
    """An empty translation falls back to the Uzbek Latin name."""
    region.name_ru = ""
    assert region.name_for("ru") == "Test viloyati"
    assert str(region) == "Test viloyati"


def test_districts_of_unknown_region_is_404(api: APIClient) -> None:
    """An unknown region is not_found, not an empty list."""
    response = api.get("/api/v1/geo/regions/1/districts")
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
