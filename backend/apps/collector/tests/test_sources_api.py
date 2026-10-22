"""Tests for GET /api/v1/sources."""

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.collector.models import CrawlSource
from apps.common.models import ReviewStatus
from apps.corpus.models import Document
from apps.geo.models import District
from apps.offices.models import Office, OfficeType

pytestmark = pytest.mark.django_db


def _source(name: str, **extra: object) -> CrawlSource:
    """Create a NAMUNA crawl source."""
    return CrawlSource.objects.create(
        name=name,
        start_url=f"https://example.org/{name}",
        publisher="example.org",
        last_crawled_at=timezone.now(),
        **extra,
    )


def _document(source: CrawlSource, status: str, slug: str) -> None:
    """Create one document of ``source`` with ``status``."""
    Document.objects.create(
        source=source,
        kind="law",
        title="NAMUNA",
        url=f"https://example.org/doc/{slug}",
        publisher="example.org",
        fetched_at=timezone.now(),
        text="NAMUNA",
        text_hash="x",
        corpus_version="test",
        status=status,
    )


def test_lists_only_sources_with_approved_content(api: APIClient, district: District) -> None:
    """Sources need an approved document or office; counts and kinds follow the contract."""
    laws = _source("laws", document_kind="law")
    _document(laws, ReviewStatus.APPROVED, "a")
    _document(laws, ReviewStatus.APPROVED, "b")
    _document(laws, ReviewStatus.PENDING, "c")
    pending_only = _source("pending", document_kind="law")
    _document(pending_only, ReviewStatus.PENDING, "d")
    _source("inactive", is_active=False)
    office_type = OfficeType.objects.create(
        code="namuna",
        name_uz_latn="NAMUNA",
        name_uz_cyrl="НАМУНА",
        name_ru="NAMUNA",
        name_en="NAMUNA",
    )
    offices = _source("offices", kind="office", office_type=office_type)
    Office.objects.create(
        office_type=office_type,
        name="NAMUNA office",
        address="NAMUNA",
        district=district,
        region=district.region,
        source=offices,
        source_url="https://example.org/o",
        data_as_of=timezone.localdate(),
        status=ReviewStatus.APPROVED,
    )

    items = api.get("/api/v1/sources").json()["items"]

    assert [(i["name"], i["kind"], i["documents"]) for i in items] == [
        ("laws", "law", 2),
        ("offices", "office", 1),
    ]
    assert items[0]["url"] == "https://example.org/laws"
    assert items[0]["publisher"] == "example.org"
    assert items[0]["last_fetched_at"]
