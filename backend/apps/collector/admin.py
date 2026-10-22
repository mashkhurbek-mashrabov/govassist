from django.contrib import admin

from apps.collector.models import CrawlJob, CrawlSource, RawPage
from apps.common.admin import BaseAdmin


@admin.register(CrawlSource)
class CrawlSourceAdmin(BaseAdmin):
    """Sources the admin wants crawled."""

    list_display = ("name", "kind", "publisher", "is_active", "last_crawled_at")
    list_filter = ("kind", "publisher", "is_active")
    search_fields = ("name", "start_url")


@admin.register(CrawlJob)
class CrawlJobAdmin(BaseAdmin):
    """Crawl runs and their outcome."""

    list_display = ("source", "status", "pages_fetched", "pages_skipped", "started_at")
    list_filter = ("status",)


@admin.register(RawPage)
class RawPageAdmin(BaseAdmin):
    """Fetched pages (bytes on disk)."""

    list_display = ("url", "http_status", "content_type", "fetched_at")
    search_fields = ("url",)
