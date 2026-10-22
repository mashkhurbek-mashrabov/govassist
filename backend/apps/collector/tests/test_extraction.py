"""Tests for the Gemini extraction wrappers with a fake client (no network)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.collector.constants import MAX_PAGE_CHARS
from apps.collector.extraction import (
    FakeOfficeTypeClassifier,
    GeminiOfficeExtractor,
    GeminiOfficeTypeClassifier,
)


def _client(text: str | None) -> MagicMock:
    """A fake genai client answering ``text``."""
    client = MagicMock()
    client.aio.models.generate_content = AsyncMock(return_value=SimpleNamespace(text=text))
    return client


def test_extractor_parses_structured_output() -> None:
    """JSON offices become candidates; the page is sent as data with the rules as system text."""
    client = _client(
        '{"offices": [{"name": "NAMUNA", "address": "NAMUNA 1", "district_name": "D", '
        '"region_name": "R", "phone": null, "working_hours": [], "latitude": null, '
        '"longitude": null}]}'
    )
    offices = GeminiOfficeExtractor(client, model="m").extract("x" * (MAX_PAGE_CHARS + 10))
    assert [office.name for office in offices] == ["NAMUNA"]
    kwargs = client.aio.models.generate_content.call_args.kwargs
    assert kwargs["contents"] == "PAGE:\n" + "x" * MAX_PAGE_CHARS
    assert "never infer" in kwargs["config"].system_instruction
    assert kwargs["config"].response_mime_type == "application/json"


def test_extractor_fails_loudly_on_bad_output() -> None:
    """Invalid JSON or empty answers raise instead of silently giving no offices."""
    with pytest.raises(ValueError, match=r"Invalid JSON|validation"):
        GeminiOfficeExtractor(_client("{oops"), model="m").extract("page")
    with pytest.raises(ValueError, match="no text"):
        GeminiOfficeExtractor(_client(None), model="m").extract("page")


@pytest.mark.parametrize(("answer", "expected"), [("tax", "tax"), ("none", None), ("bogus", None)])
def test_classifier_uses_enum_output(answer: str, expected: str | None) -> None:
    """The answer must be one of the known codes."""
    client = _client(answer)
    assert (
        GeminiOfficeTypeClassifier(client, model="m").classify("page", ["tax", "notary"])
        == expected
    )
    config = client.aio.models.generate_content.call_args.kwargs["config"]
    assert config.response_mime_type == "text/x.enum"


def test_classifier_without_codes_and_fake() -> None:
    """No codes means no call; the fake only returns offered codes."""
    client = _client("tax")
    assert GeminiOfficeTypeClassifier(client, model="m").classify("page", []) is None
    client.aio.models.generate_content.assert_not_called()
    assert FakeOfficeTypeClassifier("tax").classify("p", ["notary"]) is None
