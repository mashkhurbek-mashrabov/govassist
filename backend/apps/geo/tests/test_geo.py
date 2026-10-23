"""Tests for the geo endpoints and SOATO seeding."""

from collections.abc import Callable
from typing import Any

import pytest
from rest_framework.test import APIClient

from apps.common.constants import Lang
from apps.geo import selectors
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


def test_names_follow_ui_language_right_after_patch_me(
    auth_api: APIClient, district: District
) -> None:
    """The cache is per language: switching ui_language shows the new names at once."""
    url = f"/api/v1/geo/regions/{district.region_id}/districts"
    assert auth_api.patch("/api/v1/me", {"ui_language": "ru"}, format="json").status_code == 200
    assert auth_api.get(url).json() == [{"id": district.id, "name": "Тестовый район"}]
    response = auth_api.patch("/api/v1/me", {"ui_language": "uz-Cyrl"}, format="json")
    assert response.status_code == 200
    assert auth_api.get(url).json() == [{"id": district.id, "name": "Тест тумани"}]


def test_places_are_cached_per_language(
    district: District, django_assert_num_queries: Callable[[int], Any]
) -> None:
    """A second read in the same language hits the cache, not the database."""
    first = selectors.region_places(Lang.EN)
    with django_assert_num_queries(0):
        assert selectors.region_places(Lang.EN) == first
    assert selectors.region_places(Lang.RU) != first
