from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from apps.common.admin import BaseAdmin
from apps.offices import services
from apps.offices.maps import map_url
from apps.offices.models import Office, OfficeType, ServiceOffice


@admin.register(OfficeType)
class OfficeTypeAdmin(BaseAdmin):
    """Office types; names are the labels shown to users."""

    list_display = ("code", "name_uz_latn", "name_ru")
    search_fields = ("code", "name_uz_latn", "name_ru")


@admin.register(Office)
class OfficeAdmin(BaseAdmin):
    """Offices awaiting or past review, with map and source links."""

    list_display = (
        "name",
        "office_type",
        "district",
        "status",
        "needs_review",
        "is_active",
        "data_as_of",
    )
    list_filter = ("status", "needs_review", "office_type", "region", "is_active")
    search_fields = ("name", "address")
    autocomplete_fields = ("district", "region")
    readonly_fields = ("map_link", "source_link", "created_at", "updated_at")
    actions = ("approve", "reject")

    @admin.display(description="Map")
    def map_link(self, obj: Office) -> str:
        """Google Maps link (contract §5 ``map_url``).

        Args:
            obj: The office.
        """
        url = map_url(obj.name, obj.address, obj.latitude, obj.longitude)
        return format_html('<a href="{}" target="_blank" rel="noopener">Open map</a>', url)

    @admin.display(description="Source")
    def source_link(self, obj: Office) -> str:
        """Link to the page the office was extracted from.

        Args:
            obj: The office.
        """
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
            obj.source_url,
            obj.source_url,
        )

    @admin.action(description="Approve")
    def approve(self, request: HttpRequest, queryset: QuerySet[Office]) -> None:
        """Approve the selected offices.

        Args:
            request: The admin request.
            queryset: Selected offices.
        """
        self.message_user(
            request, f"Approved {services.approve_offices(queryset)}.", messages.SUCCESS
        )

    @admin.action(description="Reject")
    def reject(self, request: HttpRequest, queryset: QuerySet[Office]) -> None:
        """Reject the selected offices.

        Args:
            request: The admin request.
            queryset: Selected offices.
        """
        self.message_user(
            request, f"Rejected {services.reject_offices(queryset)}.", messages.WARNING
        )


@admin.register(ServiceOffice)
class ServiceOfficeAdmin(BaseAdmin):
    """Which office type handles which service page; confirm suggestions here."""

    list_display = ("document", "office_type", "confirmed")
    list_filter = ("confirmed", "office_type")
    list_editable = ("confirmed",)
    autocomplete_fields = ("document",)
