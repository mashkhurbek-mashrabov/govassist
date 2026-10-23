"""Constants of the geo app (AGENTS.md: no constant values elsewhere in the app)."""

from pathlib import Path

from django.db import models

GEO_CACHE_KEY = "geo:{scope}:{lang}"
GEO_CACHE_S = 60 * 60

SOATO_FIXTURE = Path(__file__).parent / "fixtures" / "soato.json"

NAME_FIELDS = ("name_uz_latn", "name_uz_cyrl", "name_ru")


class DistrictKind(models.TextChoices):
    """Administrative kind of the unit."""

    DISTRICT = "district", "District"
    CITY = "city", "City"
