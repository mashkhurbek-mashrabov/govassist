from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.collector.models import CrawlJob, CrawlSource, RawPage
from apps.collector.services import start_crawl
from apps.common.admin import BaseAdmin


@admin.register(CrawlSource)
class CrawlSourceAdmin(BaseAdmin):
    """Sources the admin wants crawled."""

    list_display = ("name", "kind", "document_kind", "publisher", "is_active", "last_crawled_at")
    list_filter = ("kind", "document_kind", "publisher", "is_active")
    search_fields = ("name", "start_url")
    readonly_fields = ("last_crawled_at", "created_at", "updated_at")
    filter_horizontal = ("office_regions",)
    actions = ("run_crawl",)

    @admin.action(description="Run crawl now")
    def run_crawl(self, request: HttpRequest, queryset: QuerySet[CrawlSource]) -> None:
        """Queue a crawl job per selected source for the worker.

        Args:
            request: The admin request.
            queryset: Selected sources.
        """
        jobs = [start_crawl(source) for source in queryset]
        self.message_user(request, f"Queued {len(jobs)} crawl job(s).", messages.SUCCESS)


@admin.register(CrawlJob)
class CrawlJobAdmin(BaseAdmin):
    """Crawl runs and their outcome (read-only)."""

    list_select_related = ("source",)
    list_display = ("source", "status", "pages_fetched", "pages_skipped", "started_at")
    list_filter = ("status",)
    readonly_fields = (
        "source",
        "status",
        "started_at",
        "finished_at",
        "pages_fetched",
        "pages_skipped",
        "error",
        "created_at",
        "updated_at",
    )


@admin.register(RawPage)
class RawPageAdmin(BaseAdmin):
    """Fetched pages (bytes on disk)."""

    list_display = ("url", "http_status", "content_type", "fetched_at")
    search_fields = ("url",)
