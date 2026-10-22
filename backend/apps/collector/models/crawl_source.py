import re

from django.core.exceptions import ValidationError
from django.db import models

from apps.collector.constants import DEFAULT_MAX_PAGES, CrawlSourceKind
from apps.common.models import BaseModel
from apps.corpus.constants import DocumentKind


class CrawlSource(BaseModel):
    """A start URL the admin wants crawled, plus crawl rules."""

    Kind = CrawlSourceKind

    name = models.CharField(max_length=200)
    start_url = models.URLField(max_length=1000)
    kind = models.CharField(max_length=10, choices=Kind, default=Kind.DOCUMENT)
    document_kind = models.CharField(
        max_length=20, choices=DocumentKind, default=DocumentKind.OTHER
    )
    office_type = models.ForeignKey(
        "offices.OfficeType", null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    office_regions = models.ManyToManyField(
        "geo.Region",
        blank=True,
        related_name="+",
        help_text="Office sources: keep only offices in these regions (empty: all regions).",
    )
    office_name_pattern = models.CharField(
        max_length=200,
        blank=True,
        help_text="Office sources: regex an office name must contain (case-insensitive).",
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
        """Office sources must name their office type; the name pattern must be a regex.

        Raises:
            ValidationError: When an office source has no office type, or the pattern is not
                a valid regular expression.
        """
        if self.kind == self.Kind.OFFICE and self.office_type_id is None:
            raise ValidationError({"office_type": "Required for office sources."})
        try:
            re.compile(self.office_name_pattern)
        except re.error as exc:
            raise ValidationError({"office_name_pattern": str(exc)}) from exc
