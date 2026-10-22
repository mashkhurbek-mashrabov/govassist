"""Google Maps URL generation for offices (contract §5)."""

import urllib.parse

MAPS_SEARCH_BASE_URL = "https://www.google.com/maps/search/?api=1&query="


def map_url(
    name: str,
    address: str,
    latitude: float | None,
    longitude: float | None,
) -> str:
    """Build a Google Maps link for an office by coordinates or search query.

    When both latitude and longitude are given, links directly to the
    coordinate pair. Otherwise, falls back to a search on the office name
    and address.

    Args:
        name: Office title or name.
        address: Physical street/building address.
        latitude: Latitude in WGS 84, or None.
        longitude: Longitude in WGS 84, or None.

    Returns:
        Full Google Maps search URL.
    """
    if latitude is not None and longitude is not None:
        return f"{MAPS_SEARCH_BASE_URL}{latitude},{longitude}"
    encoded_query = urllib.parse.quote(f"{name} {address}".strip())
    return f"{MAPS_SEARCH_BASE_URL}{encoded_query}"
