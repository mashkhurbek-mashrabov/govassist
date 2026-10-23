"""Tests for the LLM judge: vendor independence and the OpenAI-compatible client (mock HTTP)."""

import json

import httpx
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from pydantic import ValidationError

from apps.evaluation.constants import JUDGE_TEMPERATURE
from apps.evaluation.judge import OpenAICompatibleJudge, ensure_independent, vendor_of

BASE_URL = "https://judge.example.org/v1"


def judge_with(reply: str, seen: list[httpx.Request], status: int = 200) -> OpenAICompatibleJudge:
    """A judge whose HTTP client returns ``reply`` as the message content."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Record the request and answer like a chat-completions endpoint."""
        seen.append(request)
        return httpx.Response(status, json={"choices": [{"message": {"content": reply}}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenAICompatibleJudge(
        base_url=BASE_URL, api_key="test-key", model="judge-model", client=client
    )


def test_vendor_detection() -> None:
    """Gemini models and Google endpoints are recognized as the generator's vendor."""
    assert vendor_of("gemini-3.8-flash") == "google"
    assert vendor_of("x", "https://generativelanguage.googleapis.com/v1beta/openai") == "google"
    assert vendor_of("judge-model", BASE_URL) is None


def test_same_vendor_judge_is_refused() -> None:
    """Gemini must not grade Gemini."""
    with pytest.raises(ImproperlyConfigured, match="vendor"):
        ensure_independent("gemini-3.8-pro", BASE_URL)


def test_judge_request_and_verdict() -> None:
    """The judge sends a temperature-0 JSON request with the answer as data; parses the verdict."""
    seen: list[httpx.Request] = []
    reply = json.dumps({"correctness": 1, "grounded": False, "unsupported_claims": ["fee"]})
    verdict = judge_with(reply, seen).judge(
        question="NAMUNA?", expected_facts=["NAMUNA fact"], answer="NAMUNA answer", sources="[S1] x"
    )
    assert (verdict.correctness, verdict.grounded, verdict.unsupported_claims) == (
        1,
        False,
        ["fee"],
    )
    request = seen[0]
    assert str(request.url) == f"{BASE_URL}/chat/completions"
    assert request.headers["Authorization"] == "Bearer test-key"
    body = json.loads(request.content)
    assert body["temperature"] == JUDGE_TEMPERATURE
    assert body["response_format"] == {"type": "json_object"}
    assert "NAMUNA answer" in body["messages"][1]["content"]
    assert "NAMUNA fact" in body["messages"][1]["content"]


@pytest.mark.parametrize(
    "reply",
    [
        json.dumps({"correctness": 3, "grounded": True}),
        json.dumps({"correctness": 1, "grounded": True, "extra": 1}),
    ],
)
def test_judge_rejects_non_strict_json(reply: str) -> None:
    """Out-of-range scores and extra keys fail loudly."""
    with pytest.raises(ValidationError):
        judge_with(reply, []).judge(question="q", expected_facts=[], answer="a", sources="")


def test_judge_http_error_is_raised() -> None:
    """A non-2xx reply is an error, not a silent zero."""
    with pytest.raises(httpx.HTTPStatusError):
        judge_with("{}", [], status=500).judge(
            question="q", expected_facts=[], answer="a", sources=""
        )


def test_from_settings_needs_all_settings() -> None:
    """Without a key there is no judge."""
    with (
        override_settings(JUDGE_BASE_URL=BASE_URL, JUDGE_API_KEY="", JUDGE_MODEL="judge-model"),
        pytest.raises(ImproperlyConfigured, match="JUDGE_"),
    ):
        OpenAICompatibleJudge.from_settings()
