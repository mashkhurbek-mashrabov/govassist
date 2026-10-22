"""Tests for office extraction and service classification using mocks."""

from unittest.mock import AsyncMock, MagicMock, patch

from apps.collector.extraction import (
    FakeOfficeExtractor,
    FakeOfficeTypeClassifier,
    GeminiOfficeExtractor,
    GeminiOfficeTypeClassifier,
    OfficeCandidate,
)

NAMUNA_OFFICE_JSON = """{
  "candidates": [
    {
      "name": "NAMUNA Davlat xizmatlari markazi",
      "address": "Amir Temur koʻchasi 1",
      "district_name": "Test tumani",
      "region_name": "Test viloyati",
      "phone": "+998 71 200 00 00",
      "working_hours": [
        {
          "days": ["mon", "tue", "wed", "thu", "fri"],
          "open": "09:00",
          "close": "18:00",
          "break": {"start": "13:00", "end": "14:00"}
        }
      ],
      "latitude": 41.31,
      "longitude": 69.28
    }
  ]
}"""


def test_fake_office_extractor() -> None:
    """Verifies default and configured FakeOfficeExtractor behaviors."""
    default_extractor = FakeOfficeExtractor()
    assert default_extractor.extract("any text") == []

    candidate = OfficeCandidate(
        name="NAMUNA Markaz",
        address="Manzil 1",
        district_name="Test",
        region_name="Viloyat",
    )
    configured_extractor = FakeOfficeExtractor([candidate])
    assert configured_extractor.extract("any text") == [candidate]


def test_fake_office_type_classifier() -> None:
    """Verifies FakeOfficeTypeClassifier validates returned code against valid codes."""
    classifier = FakeOfficeTypeClassifier(result="public_service_center")
    codes = ["public_service_center", "registry"]
    assert classifier.classify("text", codes) == "public_service_center"
    assert classifier.classify("text", ["registry"]) is None


def test_gemini_office_extractor_success() -> None:
    """Verifies GeminiOfficeExtractor parses structured output into OfficeCandidate objects."""
    mock_response = MagicMock()
    mock_response.text = NAMUNA_OFFICE_JSON

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("apps.collector.extraction.get_client", return_value=mock_client):
        extractor = GeminiOfficeExtractor()
        results = extractor.extract("NAMUNA raw page text")

    assert len(results) == 1
    office = results[0]
    assert office.name == "NAMUNA Davlat xizmatlari markazi"
    assert office.address == "Amir Temur koʻchasi 1"
    assert office.district_name == "Test tumani"
    assert office.phone == "+998 71 200 00 00"
    assert len(office.working_hours) == 1
    assert office.working_hours[0].days == ["mon", "tue", "wed", "thu", "fri"]
    assert office.working_hours[0].break_ == {"start": "13:00", "end": "14:00"}
    assert office.latitude == 41.31


def test_gemini_office_extractor_invalid_json() -> None:
    """Verifies that invalid or empty JSON output from Gemini gracefully returns empty list."""
    mock_response = MagicMock()
    mock_response.text = "NOT JSON"

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("apps.collector.extraction.get_client", return_value=mock_client):
        extractor = GeminiOfficeExtractor()
        assert extractor.extract("NAMUNA page text") == []


def test_gemini_office_extractor_empty_response() -> None:
    """Verifies empty model response returns empty list."""
    mock_response = MagicMock()
    mock_response.text = ""

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("apps.collector.extraction.get_client", return_value=mock_client):
        extractor = GeminiOfficeExtractor()
        assert extractor.extract("NAMUNA page text") == []


def test_gemini_classifier_matches_code() -> None:
    """Verifies GeminiOfficeTypeClassifier returns valid matched code."""
    mock_response = MagicMock()
    mock_response.text = "public_service_center\n"

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("apps.collector.extraction.get_client", return_value=mock_client):
        classifier = GeminiOfficeTypeClassifier()
        res = classifier.classify("ID karta olish xizmati", ["public_service_center", "registry"])

    assert res == "public_service_center"


def test_gemini_classifier_unmatched_or_none() -> None:
    """Verifies GeminiOfficeTypeClassifier returns None when model outputs NONE or invalid code."""
    mock_response = MagicMock()
    mock_response.text = "NONE"

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("apps.collector.extraction.get_client", return_value=mock_client):
        classifier = GeminiOfficeTypeClassifier()
        res = classifier.classify("Qonun hujjati", ["public_service_center", "registry"])

    assert res is None


def test_gemini_classifier_empty_codes() -> None:
    """Verifies classifier returns None immediately when codes list is empty."""
    classifier = GeminiOfficeTypeClassifier()
    assert classifier.classify("Any text", []) is None
