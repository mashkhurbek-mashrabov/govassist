from django.db import models

from apps.collector.models.crawl_job import CrawlJob
from apps.common.models import BaseModel


class RawPage(BaseModel):
    """A fetched page; the bytes live on disk under ``RAW_DATA_DIR``."""

    job = models.ForeignKey(CrawlJob, on_delete=models.CASCADE, related_name="pages")
    url = models.URLField(max_length=1000)
    http_status = models.PositiveSmallIntegerField()
    content_type = models.CharField(max_length=100)
    content_hash = models.CharField(max_length=64)
    raw_path = models.CharField(max_length=500)
    fetched_at = models.DateTimeField()

    class Meta:
        ordering = ["-fetched_at"]

    def __str__(self) -> str:
        return self.url
