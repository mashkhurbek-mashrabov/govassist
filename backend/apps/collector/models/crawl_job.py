from django.db import models

from apps.collector.constants import CrawlJobStatus
from apps.collector.models.crawl_source import CrawlSource
from apps.common.models import BaseModel


class CrawlJob(BaseModel):
    """One crawl run of a source."""

    Status = CrawlJobStatus

    source = models.ForeignKey(CrawlSource, on_delete=models.CASCADE, related_name="jobs")
    status = models.CharField(max_length=10, choices=Status, default=Status.QUEUED)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    pages_fetched = models.PositiveIntegerField(default=0)
    pages_skipped = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.source} @ {self.created_at:%Y-%m-%d %H:%M}"
