from typing import Any

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.collector.constants import OFFICE_KIND, SOURCE_SUMMARY_KINDS
from apps.collector.models import CrawlSource


class SourceSummarySerializer(serializers.Serializer[Any]):
    """``SourceSummary`` of the contract (About page)."""

    publisher = serializers.CharField()
    name = serializers.CharField()
    kind = serializers.SerializerMethodField()
    url = serializers.URLField(source="start_url")
    documents = serializers.SerializerMethodField()
    last_fetched_at = serializers.DateTimeField(source="last_crawled_at", allow_null=True)

    @extend_schema_field(serializers.ChoiceField(choices=SOURCE_SUMMARY_KINDS))
    def get_kind(self, obj: CrawlSource) -> str:
        """``office`` for office sources, else the kind of the source's documents.

        Args:
            obj: An annotated source from ``public_sources``.
        """
        return OFFICE_KIND if obj.kind == CrawlSource.Kind.OFFICE else obj.document_kind

    def get_documents(self, obj: CrawlSource) -> int:
        """Approved items this source contributes (documents, or offices for office sources).

        Args:
            obj: An annotated source from ``public_sources``.
        """
        count: int = obj.office_count if obj.kind == CrawlSource.Kind.OFFICE else obj.document_count  # type: ignore[attr-defined]
        return count
