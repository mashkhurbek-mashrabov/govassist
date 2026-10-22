"""Tests for office Google Maps URL generation."""

import urllib.parse

from apps.offices.constants import MAPS_SEARCH_BASE_URL
from apps.offices.maps import map_url

NAMUNA_OFFICE_NAME = "NAMUNA Davlat xizmatlari markazi"
NAMUNA_OFFICE_ADDRESS = "Amir Temur koʻchasi 1-uy"
NAMUNA_LATITUDE = 41.311158
NAMUNA_LONGITUDE = 69.279737


def test_map_url_with_coordinates() -> None:
    """Verifies that coordinates are prioritized when present."""
    url = map_url(
        name=NAMUNA_OFFICE_NAME,
        address=NAMUNA_OFFICE_ADDRESS,
        latitude=NAMUNA_LATITUDE,
        longitude=NAMUNA_LONGITUDE,
    )
    expected = f"{MAPS_SEARCH_BASE_URL}{NAMUNA_LATITUDE},{NAMUNA_LONGITUDE}"
    assert url == expected


def test_map_url_without_coordinates() -> None:
    """Verifies fallback to URL-encoded name and address query."""
    url = map_url(
        name=NAMUNA_OFFICE_NAME,
        address=NAMUNA_OFFICE_ADDRESS,
        latitude=None,
        longitude=None,
    )
    encoded = urllib.parse.quote(f"{NAMUNA_OFFICE_NAME} {NAMUNA_OFFICE_ADDRESS}")
    expected = f"{MAPS_SEARCH_BASE_URL}{encoded}"
    assert url == expected


def test_map_url_with_partial_coordinates() -> None:
    """Verifies that missing latitude or longitude falls back to address query."""
    url_no_lon = map_url(
        name=NAMUNA_OFFICE_NAME,
        address=NAMUNA_OFFICE_ADDRESS,
        latitude=NAMUNA_LATITUDE,
        longitude=None,
    )
    url_no_lat = map_url(
        name=NAMUNA_OFFICE_NAME,
        address=NAMUNA_OFFICE_ADDRESS,
        latitude=None,
        longitude=NAMUNA_LONGITUDE,
    )
    encoded = urllib.parse.quote(f"{NAMUNA_OFFICE_NAME} {NAMUNA_OFFICE_ADDRESS}")
    expected = f"{MAPS_SEARCH_BASE_URL}{encoded}"
    assert url_no_lon == expected
    assert url_no_lat == expected
