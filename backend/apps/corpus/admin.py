from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from unfold.admin import TabularInline

from apps.common.admin import BaseAdmin
from apps.corpus import services
from apps.corpus.models import Chunk, Document
from apps.offices.models import ServiceOffice


class ChunkInline(TabularInline):  # type: ignore[misc]
    """A document's chunks (read-only, without the embedding)."""

    model = Chunk
    fields = ("order", "heading_path", "char_count", "text")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Chunks come from indexing only.

        Args:
            request: The admin request.
            obj: The parent document.
        """
        return False


class ServiceOfficeInline(TabularInline):  # type: ignore[misc]
    """Office types suggested or confirmed for a service page."""

    model = ServiceOffice
    fields = ("office_type", "confirmed")
    extra = 0


@admin.register(Document)
class DocumentAdmin(BaseAdmin):
    """Crawled documents awaiting or past review."""

    list_display = ("title", "kind", "publisher", "status", "is_active", "fetched_at")
    list_filter = ("status", "kind", "publisher", "is_active")
    search_fields = ("title", "url")
    readonly_fields = ("text_hash", "fetched_at", "created_at", "updated_at")
    inlines = (ServiceOfficeInline, ChunkInline)
    actions = ("approve", "reject", "reindex")

    @admin.action(description="Approve (and index)")
    def approve(self, request: HttpRequest, queryset: QuerySet[Document]) -> None:
        """Approve the selected documents; indexing runs on the worker.

        Args:
            request: The admin request.
            queryset: Selected documents.
        """
        count = services.approve_documents(queryset)
        self.message_user(request, f"Approved {count}; indexing queued.", messages.SUCCESS)

    @admin.action(description="Reject")
    def reject(self, request: HttpRequest, queryset: QuerySet[Document]) -> None:
        """Reject the selected documents and drop their chunks.

        Args:
            request: The admin request.
            queryset: Selected documents.
        """
        count = services.reject_documents(queryset)
        self.message_user(request, f"Rejected {count}.", messages.WARNING)

    @admin.action(description="Re-index")
    def reindex(self, request: HttpRequest, queryset: QuerySet[Document]) -> None:
        """Re-chunk and re-embed the selected approved documents.

        Args:
            request: The admin request.
            queryset: Selected documents.
        """
        count = services.reindex_documents(queryset)
        self.message_user(request, f"Re-indexing {count} approved document(s).", messages.INFO)


@admin.register(Chunk)
class ChunkAdmin(BaseAdmin):
    """Indexed chunks (read-only)."""

    list_display = ("document", "order", "heading_path", "char_count")
    search_fields = ("text",)
    exclude = ("embedding",)
