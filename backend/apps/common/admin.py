from collections.abc import Sequence
from typing import ClassVar

from unfold.admin import ModelAdmin


class BaseAdmin(ModelAdmin):  # type: ignore[misc]
    """Shared Unfold admin defaults: read-only timestamps and paging."""

    list_per_page = 50
    readonly_fields: ClassVar[Sequence[str]] = ("created_at", "updated_at")
    show_full_result_count = False
