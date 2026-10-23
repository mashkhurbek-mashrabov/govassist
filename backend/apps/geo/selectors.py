from collections.abc import Callable, Iterable

from django.core.cache import cache
from django.db.models import QuerySet

from apps.common.constants import Lang
from apps.common.models import LocalizedName
from apps.geo.constants import GEO_CACHE_KEY, GEO_CACHE_S
from apps.geo.models import District, Region

type Place = dict[str, int | str]


def regions() -> QuerySet[Region]:
    """Return all regions ordered by SOATO code."""
    return Region.objects.all()


def districts_of(region_id: int) -> QuerySet[District]:
    """Return the districts of one region ordered by SOATO code.

    Args:
        region_id: The region's SOATO code.
    """
    return District.objects.filter(region_id=region_id)


def region_exists(region_id: int) -> bool:
    """True when ``region_id`` is a known SOATO region.

    Args:
        region_id: The region's SOATO code.
    """
    return Region.objects.filter(id=region_id).exists()


def _places(units: Iterable[LocalizedName], lang: Lang) -> list[Place]:
    """``[{id, name}]`` with names in ``lang`` (contract ``Region`` / ``District``)."""
    return [{"id": unit.pk, "name": unit.name_for(lang)} for unit in units]


def _cached(key: str, build: Callable[[], list[Place]]) -> list[Place]:
    """The cached places under ``key``, built and stored for ``GEO_CACHE_S`` on a miss."""
    places: list[Place] | None = cache.get(key)
    if places is None:
        places = build()
        cache.set(key, places, GEO_CACHE_S)
    return places


def region_places(lang: Lang) -> list[Place]:
    """All regions as ``{id, name}`` in ``lang``, cached per language.

    The cache key holds the language, so a user who switches ``ui_language`` gets the new
    names at once (a page cache keyed by the session cookie served the old ones).

    Args:
        lang: The language to localize names in.
    """
    return _cached(
        GEO_CACHE_KEY.format(scope="regions", lang=lang), lambda: _places(regions(), lang)
    )


def district_places(region_id: int, lang: Lang) -> list[Place]:
    """A region's districts as ``{id, name}`` in ``lang``, cached per region and language.

    Args:
        region_id: The region's SOATO code.
        lang: The language to localize names in.
    """
    return _cached(
        GEO_CACHE_KEY.format(scope=f"districts:{region_id}", lang=lang),
        lambda: _places(districts_of(region_id), lang),
    )
