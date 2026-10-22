from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import BaseModel
from apps.corpus.models import DocumentKind

DEFAULT_MAX_PAGES = 20


class CrawlSource(BaseModel):
    """A start URL the admin wants crawled, plus crawl rules."""

    class Kind(models.TextChoices):
        """What the pages of this source become."""

        DOCUMENT = "document", "Documents (RAG corpus)"
        OFFICE = "office", "Offices (directory)"

    name = models.CharField(max_length=200)
    start_url = models.URLField(max_length=1000)
    kind = models.CharField(max_length=10, choices=Kind, default=Kind.DOCUMENT)
    document_kind = models.CharField(
        max_length=20, choices=DocumentKind, default=DocumentKind.OTHER
    )
    office_type = models.ForeignKey(
        "offices.OfficeType", null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    allowed_url_pattern = models.CharField(
        max_length=500, blank=True, help_text="Regex; links matching it are followed."
    )
    max_pages = models.PositiveIntegerField(default=DEFAULT_MAX_PAGES)
    use_browser = models.BooleanField(default=False)
    publisher = models.CharField(max_length=100)
    terms_note = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    last_crawled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        """Office sources must name the office type they list.

        Raises:
            ValidationError: When an office source has no office type.
        """
        if self.kind == self.Kind.OFFICE and self.office_type_id is None:
            raise ValidationError({"office_type": "Required for office sources."})


class CrawlJob(BaseModel):
    """One crawl run of a source."""

    class Status(models.TextChoices):
        """Lifecycle of a crawl job."""

        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

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
