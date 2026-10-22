from django.db.models import QuerySet

from apps.geo.models import District, Region


def regions() -> QuerySet[Region]:
    """Return all regions ordered by SOATO code."""
    return Region.objects.all()


def districts_of(region_id: int) -> QuerySet[District]:
    """Return the districts of one region ordered by SOATO code.

    Args:
        region_id: The region's SOATO code.
    """
    return District.objects.filter(region_id=region_id)
