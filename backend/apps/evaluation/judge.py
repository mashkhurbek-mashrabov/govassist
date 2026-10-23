"""The LLM judge (plan §7): a different vendor than the Gemini generator, temperature 0.

The real judge talks to any OpenAI-compatible chat-completions endpoint configured by
``JUDGE_BASE_URL`` / ``JUDGE_API_KEY`` / ``JUDGE_MODEL``. Its reply must be the strict JSON of
``JudgeVerdict``. The answer under test is data for the judge, never instructions.
"""

import json
from collections.abc import Sequence
from typing import Protocol

import httpx
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from apps.evaluation.constants import (
    GENERATOR_VENDOR,
    JUDGE_SYSTEM,
    JUDGE_TEMPERATURE,
    VENDOR_HINTS,
)
from apps.evaluation.schemas import JudgeVerdict


class Judge(Protocol):
    """Scores one answer against the expected facts and the retrieved sources."""

    model: str

    def judge(
        self, *, question: str, expected_facts: Sequence[str], answer: str, sources: str
    ) -> JudgeVerdict:
        """Return the verdict for one answer."""
        ...


def vendor_of(*names: str) -> str | None:
    """The known vendor a model name or endpoint belongs to, or None.

    Args:
        *names: Model names and/or base URLs.
    """
    text = " ".join(names)
    return next((vendor for vendor, hint in VENDOR_HINTS.items() if hint.search(text)), None)


def ensure_independent(judge_model: str, base_url: str) -> None:
    """Refuse a judge from the generator's own vendor (Gemini must not grade Gemini).

    Args:
        judge_model: The judge model name.
        base_url: The judge endpoint.

    Raises:
        ImproperlyConfigured: When the judge is a Google/Gemini model or endpoint.
    """
    if vendor_of(judge_model, base_url) == GENERATOR_VENDOR:
        msg = f"The judge ({judge_model} at {base_url}) is from the generator's vendor."
        raise ImproperlyConfigured(msg)


def _user_message(question: str, expected_facts: Sequence[str], answer: str, sources: str) -> str:
    """The judge's input, with every part fenced as data."""
    facts = "\n".join(f"- {fact}" for fact in expected_facts) or "(none given)"
    return (
        f"QUESTION:\n{question}\n\nEXPECTED FACTS:\n{facts}\n\n"
        f"SOURCES:\n{sources or '(none)'}\n\nANSWER:\n{answer}"
    )


class OpenAICompatibleJudge:
    """A judge served by an OpenAI-compatible ``/chat/completions`` endpoint.

    Construct with :meth:`from_settings` in production; tests inject an ``httpx.Client``
    with a mock transport.
    """

    def __init__(self, *, base_url: str, api_key: str, model: str, client: httpx.Client) -> None:
        ensure_independent(model, base_url)
        self.model = model
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._client = client

    @classmethod
    def from_settings(cls) -> OpenAICompatibleJudge:
        """Build the judge from ``JUDGE_*`` settings.

        Raises:
            ImproperlyConfigured: When any setting is missing or the vendor is the generator's.
        """
        if not (settings.JUDGE_BASE_URL and settings.JUDGE_API_KEY and settings.JUDGE_MODEL):
            msg = "Set JUDGE_BASE_URL, JUDGE_API_KEY and JUDGE_MODEL to use the judge."
            raise ImproperlyConfigured(msg)
        return cls(
            base_url=settings.JUDGE_BASE_URL,
            api_key=settings.JUDGE_API_KEY,
            model=settings.JUDGE_MODEL,
            client=httpx.Client(timeout=settings.JUDGE_TIMEOUT_S),
        )

    def judge(
        self, *, question: str, expected_facts: Sequence[str], answer: str, sources: str
    ) -> JudgeVerdict:
        """Ask the judge once and validate its JSON strictly.

        Args:
            question: The test question.
            expected_facts: Gold facts.
            answer: The answer text under test.
            sources: The retrieved sources shown to the generator ("" without RAG).

        Raises:
            httpx.HTTPStatusError: On a non-2xx reply.
            pydantic.ValidationError: When the reply is not the verdict JSON.
        """
        body = {
            "model": self.model,
            "temperature": JUDGE_TEMPERATURE,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": JUDGE_SYSTEM},
                {
                    "role": "user",
                    "content": _user_message(question, expected_facts, answer, sources),
                },
            ],
        }
        response = self._client.post(self._url, json=body, headers=self._headers)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return JudgeVerdict.model_validate(json.loads(content))


class FakeJudge:
    """Deterministic judge for tests: a fixed verdict, and the calls it received."""

    model = "fake-judge"

    def __init__(self, verdict: JudgeVerdict | None = None) -> None:
        self.verdict = verdict or JudgeVerdict(correctness=2, grounded=True)
        self.calls: list[dict[str, str]] = []

    def judge(
        self, *, question: str, expected_facts: Sequence[str], answer: str, sources: str
    ) -> JudgeVerdict:
        """Record the call and return the fixed verdict."""
        self.calls.append({"question": question, "answer": answer, "sources": sources})
        return self.verdict
