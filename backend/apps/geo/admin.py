from django.contrib import admin

from apps.common.admin import BaseAdmin
from apps.geo.models import District, Region


@admin.register(Region)
class RegionAdmin(BaseAdmin):
    """Regions (read mostly; seeded from SOATO)."""

    list_display = ("id", "name_uz_latn", "name_ru")
    search_fields = ("id", "name_uz_latn", "name_uz_cyrl", "name_ru")
    readonly_fields = ()


@admin.register(District)
class DistrictAdmin(BaseAdmin):
    """Districts and district-level cities (seeded from SOATO)."""

    list_display = ("id", "name_uz_latn", "region", "kind")
    list_filter = ("region", "kind")
    search_fields = ("id", "name_uz_latn", "name_uz_cyrl", "name_ru")
    readonly_fields = ()
