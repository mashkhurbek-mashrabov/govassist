from django.contrib import admin

from apps.common.admin import BaseAdmin
from apps.corpus.models import Chunk, Document


@admin.register(Document)
class DocumentAdmin(BaseAdmin):
    """Crawled documents awaiting or past review."""

    list_display = ("title", "kind", "publisher", "status", "is_active", "fetched_at")
    list_filter = ("status", "kind", "publisher", "is_active")
    search_fields = ("title", "url")


@admin.register(Chunk)
class ChunkAdmin(BaseAdmin):
    """Indexed chunks (read-only)."""

    list_display = ("document", "order", "heading_path", "char_count")
    search_fields = ("text",)
    exclude = ("embedding",)
