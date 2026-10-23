"""Tests for DocumentPipeline and OfficePipeline (fake Gemini collaborators)."""

from datetime import date, datetime

import pytest
from django.utils import timezone

from apps.collector.extraction import FakeOfficeExtractor, FakeOfficeTypeClassifier, OfficeCandidate
from apps.collector.models import CrawlSource
from apps.collector.parsers import ParsedPage
from apps.collector.pipelines import DocumentPipeline, OfficePipeline, find_regions
from apps.common.constants import ReviewStatus
from apps.corpus.models import Chunk, Document
from apps.geo.models import District
from apps.offices.hours import WorkingHours
from apps.offices.models import Office, OfficeType, ServiceOffice

pytestmark = pytest.mark.django_db
URL = "https://example.org/service/1"
NOW = datetime(2026, 10, 22, 9, 0, tzinfo=timezone.get_current_timezone())


def _source(**extra: object) -> CrawlSource:
    """A NAMUNA service-page source."""
    defaults: dict[str, object] = {
        "name": "NAMUNA",
        "start_url": URL,
        "publisher": "example.org",
        "document_kind": "service_page",
    }
    return CrawlSource.objects.create(**(defaults | extra))


def _page(text: str = "NAMUNA pasport almashtirish uchun ariza topshiriladi.") -> ParsedPage:
    """A parsed NAMUNA page."""
    return ParsedPage(
        title="NAMUNA xizmat", text=text, section_label="NAMUNA-1", published_at=date(2024, 1, 1)
    )


def test_document_created_pending_with_office_type_suggestion(office_type: OfficeType) -> None:
    """New pages become pending documents; service pages get an unconfirmed office type."""
    DocumentPipeline(FakeOfficeTypeClassifier(office_type.code)).process(
        _source(), _page(), url=URL, fetched_at=NOW
    )
    document = Document.objects.get(url=URL)
    assert (document.status, document.kind, document.language) == (
        "pending",
        "service_page",
        "uz-Latn",
    )
    assert (document.section_label, document.publisher) == ("NAMUNA-1", "example.org")
    mapping = ServiceOffice.objects.get(document=document)
    assert (mapping.office_type, mapping.confirmed) == (office_type, False)


def test_changed_text_sends_document_back_to_review(office_type: OfficeType) -> None:
    """New text resets an approved document to pending and drops its chunks; same text keeps it."""
    source, pipeline = _source(), DocumentPipeline(FakeOfficeTypeClassifier(None))
    pipeline.process(source, _page(), url=URL, fetched_at=NOW)
    document = Document.objects.get(url=URL)
    Document.objects.filter(id=document.id).update(status=ReviewStatus.APPROVED)
    Chunk.objects.create(document=document, order=0, text="x", text_normalized="x", char_count=1)

    pipeline.process(source, _page(), url=URL, fetched_at=NOW)
    assert Document.objects.get(id=document.id).status == ReviewStatus.APPROVED

    pipeline.process(source, _page("NAMUNA yangi matn."), url=URL, fetched_at=NOW)
    document.refresh_from_db()
    assert document.status == ReviewStatus.PENDING
    assert not document.chunks.exists()
    assert not ServiceOffice.objects.exists()


def test_laws_are_not_classified() -> None:
    """Only service pages ask the classifier."""

    class Exploding(FakeOfficeTypeClassifier):
        """Fails when called."""

        def classify(self, text: str, codes: object) -> str | None:
            """Never called for laws."""
            raise AssertionError

    DocumentPipeline(Exploding()).process(
        _source(document_kind="law"), _page(), url=URL, fetched_at=NOW
    )
    assert Document.objects.get(url=URL).kind == "law"


def _candidate(**extra: object) -> OfficeCandidate:
    """A NAMUNA office in the test district."""
    data: dict[str, object] = {
        "name": "NAMUNA markaz",
        "address": "NAMUNA koʻchasi, 1",
        "district_name": "Test tumani",
        "region_name": "Test viloyati",
        "phone": "+998 71 000 00 00",
        "working_hours": [
            WorkingHours.model_validate({"days": ["mon"], "open": "09:00", "close": "18:00"})
        ],
    }
    return OfficeCandidate.model_validate(data | extra)


def test_office_pipeline_matches_places_dedupes_and_skips(
    office_type: OfficeType, district: District
) -> None:
    """Matched offices are stored pending; duplicates and unmatched places are skipped."""
    source = _source(kind="office", office_type=office_type)
    extractor = FakeOfficeExtractor(
        [
            _candidate(),
            _candidate(name="NAMUNA dublikat", address="namuna koʻchasi 1"),
            _candidate(name="NAMUNA kirill", district_name="Тест тумани", address="NAMUNA 2"),
            _candidate(name="NAMUNA yoʻq", district_name="Mavjud emas", address="NAMUNA 3"),
            _candidate(name="NAMUNA region", region_name="Boshqa joy", address="NAMUNA 4"),
        ]
    )
    OfficePipeline(extractor).process(source, _page("NAMUNA ro'yxat"), url=URL, fetched_at=NOW)
    offices = {office.name: office for office in Office.objects.all()}
    assert set(offices) == {"NAMUNA markaz", "NAMUNA kirill"}
    office = offices["NAMUNA markaz"]
    assert (office.status, office.district, office.data_as_of) == ("pending", district, NOW.date())
    assert office.working_hours == [
        {"days": ["mon"], "open": "09:00", "close": "18:00", "break": None}
    ]
    assert extractor.texts == ["NAMUNA ro'yxat"]


def test_office_pipeline_requires_office_type() -> None:
    """An office source without a type fails loudly."""
    with pytest.raises(ValueError, match="office_type"):
        OfficePipeline(FakeOfficeExtractor()).process(
            _source(kind="office"), _page(), url=URL, fetched_at=NOW
        )


def test_find_regions_by_any_name(district: District) -> None:
    """Regions match by any language, with or without 'viloyati'."""
    assert find_regions("Тест вилояти") == [district.region]
    assert find_regions("Test region") == [district.region]  # English name (name_en)
    assert find_regions("test") == [district.region]
    assert find_regions("") == []


def test_classifier_failure_still_stores_the_document(caplog: pytest.LogCaptureFixture) -> None:
    """A Gemini outage during the suggestion is logged and the document is kept."""

    class Down(FakeOfficeTypeClassifier):
        """Raises like a 503."""

        def classify(self, text: str, codes: object) -> str | None:
            """Fail."""
            raise ConnectionError("503")

    DocumentPipeline(Down()).process(_source(), _page(), url=URL, fetched_at=NOW)
    assert Document.objects.filter(url=URL, status="pending").exists()
    assert "Office type suggestion failed" in caplog.text


def test_fuzzy_district_match_is_flagged(office_type: OfficeType, district: District) -> None:
    """A difflib-only district match is stored with needs_review=True; exact ones are not."""
    District.objects.create(
        id=9901203,
        region=district.region,
        name_uz_latn="Chilonzor tumani",
        name_uz_cyrl="Чилонзор тумани",
        name_ru="Чиланзарский район",
        name_en="Chilonzor",
    )
    source = _source(kind="office", office_type=office_type)
    extractor = FakeOfficeExtractor(
        [
            _candidate(name="NAMUNA aniq", district_name="Chilonzor tumani", address="NAMUNA 5"),
            _candidate(
                name="NAMUNA taxminiy", district_name="Chilonzorr tumani", address="NAMUNA 6"
            ),
        ]
    )
    OfficePipeline(extractor).process(source, _page("NAMUNA"), url=URL, fetched_at=NOW)
    flags = dict(Office.objects.values_list("name", "needs_review"))
    assert flags == {"NAMUNA aniq": False, "NAMUNA taxminiy": True}


def test_gemini_is_never_called_inside_a_transaction(
    office_type: OfficeType, district: District
) -> None:
    """Extractor and classifier run with no transaction open (no locks held over HTTP)."""
    from django.db import connection  # noqa: PLC0415

    seen: list[bool] = []

    class Extractor(FakeOfficeExtractor):
        """Records whether a transaction is open."""

        def extract(self, text: str) -> list[OfficeCandidate]:
            """Record, then return one office."""
            seen.append(connection.in_atomic_block)
            return [_candidate()]

    class Classifier(FakeOfficeTypeClassifier):
        """Records whether a transaction is open."""

        def classify(self, text: str, codes: object) -> str | None:
            """Record, then suggest nothing."""
            seen.append(connection.in_atomic_block)
            return None

    in_test_transaction = connection.in_atomic_block  # pytest-django wraps each test
    OfficePipeline(Extractor()).process(
        _source(kind="office", office_type=office_type), _page("NAMUNA"), url=URL, fetched_at=NOW
    )
    DocumentPipeline(Classifier()).process(_source(), _page(), url=URL, fetched_at=NOW)
    assert seen == [in_test_transaction, in_test_transaction]
    assert Office.objects.count() == 1
