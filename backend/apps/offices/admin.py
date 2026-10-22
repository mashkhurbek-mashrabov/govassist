from django.contrib import admin

from apps.common.admin import BaseAdmin
from apps.offices.models import Office, OfficeType, ServiceOffice


@admin.register(OfficeType)
class OfficeTypeAdmin(BaseAdmin):
    """Office types; names are the labels shown to users."""

    list_display = ("code", "name_uz_latn", "name_ru")
    search_fields = ("code", "name_uz_latn", "name_ru")


@admin.register(Office)
class OfficeAdmin(BaseAdmin):
    """Offices awaiting or past review."""

    list_display = ("name", "office_type", "district", "status", "is_active", "data_as_of")
    list_filter = ("status", "office_type", "region", "is_active")
    search_fields = ("name", "address")
    autocomplete_fields = ("district", "region")


@admin.register(ServiceOffice)
class ServiceOfficeAdmin(BaseAdmin):
    """Which office type handles which service page."""

    list_display = ("document", "office_type", "confirmed")
    list_filter = ("confirmed", "office_type")
    list_editable = ("confirmed",)
