from django.db import models

from apps.common.constants import Lang, ReviewStatus
from apps.common.models import BaseModel
from apps.corpus.constants import DocumentKind


class Document(BaseModel):
    """A crawled page or act, reviewed by the admin before it is indexed."""

    source = models.ForeignKey(
        "collector.CrawlSource",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="documents",
    )
    kind = models.CharField(max_length=20, choices=DocumentKind, default=DocumentKind.OTHER)
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000, unique=True)
    publisher = models.CharField(max_length=100)
    language = models.CharField(max_length=8, choices=Lang, default=Lang.UZ_LATN)
    section_label = models.CharField(max_length=200, null=True, blank=True)  # noqa: DJ001
    published_at = models.DateField(null=True, blank=True)
    fetched_at = models.DateTimeField()
    text = models.TextField()
    text_hash = models.CharField(max_length=64)
    corpus_version = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=ReviewStatus, default=ReviewStatus.PENDING)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-fetched_at"]

    def __str__(self) -> str:
        return self.title
