"""Unit tests for document and office collector pipelines."""

from datetime import UTC, datetime

import pytest

from apps.collector.extraction import (
    FakeOfficeExtractor,
    FakeOfficeTypeClassifier,
    OfficeCandidate,
    WorkingHoursOut,
)
from apps.collector.fetchers import FetchResult
from apps.collector.models import CrawlSource
from apps.collector.pipelines import DocumentPipeline, OfficePipeline, find_region
from apps.common.models import ReviewStatus
from apps.corpus.models import Chunk, Document, DocumentKind
from apps.geo.models import District, Region
from apps.offices.models import Office, OfficeType, ServiceOffice


@pytest.mark.django_db
def test_find_region_matches(region: Region) -> None:
    """Verifies find_region matches Latin, Cyrillic, Russian, and stripped suffixes."""
    assert find_region("Test viloyati") == region
    assert find_region("Test") == region
    assert find_region("Тест вилояти") == region
    assert find_region("Тестовая область") == region


@pytest.mark.django_db
def test_find_region_unknown_or_empty(region: Region) -> None:
    """Verifies find_region returns None for unknown, empty, or stripped inputs."""
    assert find_region("Mavjud emas viloyati") is None
    assert find_region("") is None
    assert find_region("   ") is None
    assert find_region("---") is None


@pytest.mark.django_db
def test_document_pipeline_create_new() -> None:
    """Verifies DocumentPipeline creates a new Document when URL does not exist."""
    source = CrawlSource.objects.create(
        name="NAMUNA Qonunchilik",
        start_url="https://example.uz/docs",
        kind=CrawlSource.Kind.DOCUMENT,
        document_kind=DocumentKind.LAW,
        publisher="Adliya vazirligi",
    )
    html_body = (
        b"<!DOCTYPE html><html><head><title>NAMUNA Qonun</title></head>"
        b"<body><main><h1>NAMUNA Qonun sarlavhasi</h1>"
        b"<p>O'zbekiston Respublikasi qonuni matni.</p></main></body></html>"
    )
    fetch_result = FetchResult(
        url="https://example.uz/docs/1",
        final_url="https://example.uz/docs/1",
        status=200,
        content_type="text/html",
        body=html_body,
    )
    now = datetime(2026, 10, 22, 12, 0, tzinfo=UTC)

    pipeline = DocumentPipeline()
    pipeline.process(source, fetch_result, url=fetch_result.url, fetched_at=now)

    doc = Document.objects.get(url="https://example.uz/docs/1")
    assert doc.title == "NAMUNA Qonun sarlavhasi"
    assert "O'zbekiston Respublikasi qonuni matni" in doc.text
    assert doc.source == source
    assert doc.kind == DocumentKind.LAW
    assert doc.publisher == "Adliya vazirligi"
    assert doc.status == ReviewStatus.PENDING
    assert doc.is_active is True
    assert doc.fetched_at == now
    assert len(doc.text_hash) == 64


@pytest.mark.django_db
def test_document_pipeline_update_unchanged() -> None:
    """Verifies DocumentPipeline retains review status and chunks when text is unchanged."""
    source = CrawlSource.objects.create(
        name="NAMUNA Qonunchilik",
        start_url="https://example.uz/docs",
        kind=CrawlSource.Kind.DOCUMENT,
        document_kind=DocumentKind.LAW,
        publisher="Adliya vazirligi",
    )
    html_body = (
        b"<!DOCTYPE html><html><head><title>NAMUNA Hujjat</title></head>"
        b"<body><main><p>O'zgarmas matn mazmuni.</p></main></body></html>"
    )
    fetch_result = FetchResult(
        url="https://example.uz/docs/2",
        final_url="https://example.uz/docs/2",
        status=200,
        content_type="text/html",
        body=html_body,
    )

    pipeline = DocumentPipeline()
    pipeline.process(
        source,
        fetch_result,
        url=fetch_result.url,
        fetched_at=datetime(2026, 10, 22, 10, 0, tzinfo=UTC),
    )

    doc = Document.objects.get(url="https://example.uz/docs/2")
    doc.status = ReviewStatus.APPROVED
    doc.save()

    chunk = Chunk.objects.create(
        document=doc,
        order=0,
        heading_path="Bosh",
        text="O'zgarmas matn mazmuni.",
        text_normalized="ozgarmas matn mazmuni",
        char_count=23,
    )

    # Process again with identical body
    later = datetime(2026, 10, 22, 14, 0, tzinfo=UTC)
    pipeline.process(source, fetch_result, url=fetch_result.url, fetched_at=later)

    doc.refresh_from_db()
    assert doc.status == ReviewStatus.APPROVED
    assert doc.fetched_at == later
    assert Chunk.objects.filter(id=chunk.id).exists()


@pytest.mark.django_db
def test_document_pipeline_update_changed_text() -> None:
    """Verifies DocumentPipeline clears chunks and resets to pending when text changes."""
    source = CrawlSource.objects.create(
        name="NAMUNA Qonunchilik",
        start_url="https://example.uz/docs",
        kind=CrawlSource.Kind.DOCUMENT,
        document_kind=DocumentKind.LAW,
        publisher="Adliya vazirligi",
    )
    body_v1 = b"<html><body><p>Eski tahrir matni.</p></body></html>"
    fetch_result_v1 = FetchResult(
        url="https://example.uz/docs/3",
        final_url="https://example.uz/docs/3",
        status=200,
        content_type="text/html",
        body=body_v1,
    )

    pipeline = DocumentPipeline()
    pipeline.process(
        source,
        fetch_result_v1,
        url=fetch_result_v1.url,
        fetched_at=datetime(2026, 10, 22, 10, 0, tzinfo=UTC),
    )

    doc = Document.objects.get(url="https://example.uz/docs/3")
    doc.status = ReviewStatus.APPROVED
    doc.save()

    Chunk.objects.create(
        document=doc,
        order=0,
        heading_path="Bosh",
        text="Eski tahrir matni.",
        text_normalized="eski tahrir matni",
        char_count=18,
    )

    # Process modified body
    body_v2 = b"<html><body><p>Yangi tahrir matni qo'shildi.</p></body></html>"
    fetch_result_v2 = FetchResult(
        url="https://example.uz/docs/3",
        final_url="https://example.uz/docs/3",
        status=200,
        content_type="text/html",
        body=body_v2,
    )
    pipeline.process(
        source,
        fetch_result_v2,
        url=fetch_result_v2.url,
        fetched_at=datetime(2026, 10, 22, 15, 0, tzinfo=UTC),
    )

    doc.refresh_from_db()
    assert doc.status == ReviewStatus.PENDING
    assert "Yangi tahrir" in doc.text
    assert not Chunk.objects.filter(document=doc).exists()


@pytest.mark.django_db
def test_document_pipeline_service_page_links_office_type() -> None:
    """Verifies service pages link classified office types with unconfirmed status."""
    office_type = OfficeType.objects.create(
        code="public_service_center",
        name_uz_latn="Davlat xizmatlari markazi",
        name_uz_cyrl="Давлат хизматлари маркази",
        name_ru="Центр государственных услуг",
        name_en="Public Service Center",
    )
    source = CrawlSource.objects.create(
        name="NAMUNA Xizmatlar",
        start_url="https://my.gov.uz",
        kind=CrawlSource.Kind.DOCUMENT,
        document_kind=DocumentKind.SERVICE_PAGE,
        publisher="my.gov.uz",
    )
    fetch_result = FetchResult(
        url="https://my.gov.uz/service/1",
        final_url="https://my.gov.uz/service/1",
        status=200,
        content_type="text/html",
        body=(
            b"<html><body><h1>Tadbirkorlikni ro'yxatdan o'tkazish</h1>"
            b"<p>DXM orqali.</p></body></html>"
        ),
    )

    classifier = FakeOfficeTypeClassifier(result="public_service_center")
    pipeline = DocumentPipeline(classifier=classifier)
    pipeline.process(
        source,
        fetch_result,
        url=fetch_result.url,
        fetched_at=datetime.now(UTC),
    )

    doc = Document.objects.get(url="https://my.gov.uz/service/1")
    link = ServiceOffice.objects.filter(document=doc, office_type=office_type).first()
    assert link is not None
    assert link.confirmed is False


@pytest.mark.django_db
def test_document_pipeline_service_page_unmatched_classifier() -> None:
    """Verifies no ServiceOffice created when classifier returns None or unknown code."""
    OfficeType.objects.create(
        code="tax_inspection",
        name_uz_latn="Soliq",
        name_uz_cyrl="Солиқ",
        name_ru="Налоговая",
        name_en="Tax",
    )
    source = CrawlSource.objects.create(
        name="NAMUNA Xizmatlar",
        start_url="https://my.gov.uz",
        kind=CrawlSource.Kind.DOCUMENT,
        document_kind=DocumentKind.SERVICE_PAGE,
        publisher="my.gov.uz",
    )
    fetch_result = FetchResult(
        url="https://my.gov.uz/service/2",
        final_url="https://my.gov.uz/service/2",
        status=200,
        content_type="text/html",
        body=b"<html><body><h1>Boshqa xizmat</h1></body></html>",
    )

    classifier = FakeOfficeTypeClassifier(result="unknown_code")
    pipeline = DocumentPipeline(classifier=classifier)
    pipeline.process(
        source,
        fetch_result,
        url=fetch_result.url,
        fetched_at=datetime.now(UTC),
    )

    doc = Document.objects.get(url="https://my.gov.uz/service/2")
    assert not ServiceOffice.objects.filter(document=doc).exists()


@pytest.mark.django_db
def test_office_pipeline_no_office_type(caplog: pytest.LogCaptureFixture) -> None:
    """Verifies OfficePipeline logs error and exits if source has no office_type."""
    source = CrawlSource.objects.create(
        name="NAMUNA Idoralar",
        start_url="https://example.uz/offices",
        kind=CrawlSource.Kind.OFFICE,
        office_type=None,
        publisher="stat.uz",
    )
    fetch_result = FetchResult(
        url="https://example.uz/offices/1",
        final_url="https://example.uz/offices/1",
        status=200,
        content_type="text/html",
        body=b"<html><body>Ofislar ro'yxati</body></html>",
    )

    extractor = FakeOfficeExtractor(
        candidates=[
            OfficeCandidate(
                name="DXM",
                address="Ko'cha 1",
                district_name="Test",
                region_name="Test",
            )
        ]
    )
    pipeline = OfficePipeline(extractor=extractor)
    pipeline.process(
        source,
        fetch_result,
        url=fetch_result.url,
        fetched_at=datetime.now(UTC),
    )

    assert "has no office_type configured" in caplog.text
    assert Office.objects.count() == 0


@pytest.mark.django_db
def test_office_pipeline_creates_and_deduplicates(region: Region, district: District) -> None:
    """Verifies OfficePipeline creates offices and deduplicates by canonical address."""
    office_type = OfficeType.objects.create(
        code="public_service_center",
        name_uz_latn="Davlat xizmatlari markazi",
        name_uz_cyrl="Давлат хизматлари маркази",
        name_ru="Центр государственных услуг",
        name_en="Public Service Center",
    )
    source = CrawlSource.objects.create(
        name="NAMUNA Idoralar",
        start_url="https://example.uz/offices",
        kind=CrawlSource.Kind.OFFICE,
        office_type=office_type,
        publisher="stat.uz",
    )
    fetch_result = FetchResult(
        url="https://example.uz/offices/1",
        final_url="https://example.uz/offices/1",
        status=200,
        content_type="text/html",
        body=b"<html><body>NAMUNA Ofislar ro'yxati</body></html>",
    )

    candidates = [
        OfficeCandidate(
            name="NAMUNA Test DXM",
            address="Amir Temur ko'chasi, 10-uy",
            district_name="Test tumani",
            region_name="Test viloyati",
            phone="+998711234567",
            working_hours=[
                WorkingHoursOut(days=["mon", "tue", "wed"], open="09:00", close="18:00")
            ],
            latitude=41.31,
            longitude=69.24,
        ),
        # Duplicate with punctuation and spacing differences
        OfficeCandidate(
            name="NAMUNA Test DXM Takroriy",
            address="Amir  Temur  ko‘chasi, 10 - uy",
            district_name="Test tumani",
            region_name="Test viloyati",
            phone="+998711234567",
        ),
    ]

    extractor = FakeOfficeExtractor(candidates=candidates)
    pipeline = OfficePipeline(extractor=extractor)
    fetch_date = datetime(2026, 10, 22, 12, 0, tzinfo=UTC)
    pipeline.process(
        source,
        fetch_result,
        url=fetch_result.url,
        fetched_at=fetch_date,
    )

    assert Office.objects.count() == 1
    office = Office.objects.first()
    assert office is not None
    assert office.name == "NAMUNA Test DXM"
    assert office.district == district
    assert office.region == region
    assert office.phone == "+998711234567"
    assert office.latitude == 41.31
    assert office.longitude == 69.24
    assert office.data_as_of == fetch_date.date()
    assert office.status == ReviewStatus.PENDING
    assert office.is_active is True
    assert len(office.working_hours) == 1


@pytest.mark.django_db
def test_office_pipeline_skips_unmatched_region_and_district(
    region: Region, district: District
) -> None:
    """Verifies candidates with unresolvable regions or districts are skipped."""
    office_type = OfficeType.objects.create(
        code="public_service_center",
        name_uz_latn="Davlat xizmatlari markazi",
        name_uz_cyrl="Давлат хизматлари маркази",
        name_ru="Центр государственных услуг",
        name_en="Public Service Center",
    )
    source = CrawlSource.objects.create(
        name="NAMUNA Idoralar",
        start_url="https://example.uz/offices",
        kind=CrawlSource.Kind.OFFICE,
        office_type=office_type,
        publisher="stat.uz",
    )
    fetch_result = FetchResult(
        url="https://example.uz/offices/2",
        final_url="https://example.uz/offices/2",
        status=200,
        content_type="text/html",
        body=b"<html><body>NAMUNA Ofislar</body></html>",
    )

    candidates = [
        OfficeCandidate(
            name="NAMUNA Noma'lum Viloyat DXM",
            address="Ko'cha 1",
            district_name="Test tumani",
            region_name="Noma'lum viloyat",
        ),
        OfficeCandidate(
            name="NAMUNA Noma'lum Tuman DXM",
            address="Ko'cha 2",
            district_name="Noma'lum tumani",
            region_name="Test viloyati",
        ),
    ]

    extractor = FakeOfficeExtractor(candidates=candidates)
    pipeline = OfficePipeline(extractor=extractor)
    pipeline.process(
        source,
        fetch_result,
        url=fetch_result.url,
        fetched_at=datetime.now(UTC),
    )

    assert Office.objects.count() == 0
