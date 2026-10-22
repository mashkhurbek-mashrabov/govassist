"""Answer generation port: Gemini streaming JSON, plus a scripted fake for tests (plan §11)."""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

from django.conf import settings
from google import genai
from google.genai import types

from apps.chat.prompts import Prompt
from apps.chat.schemas import Answer
from apps.common.gemini import backoff_delay, get_client, is_retryable


@dataclass
class Usage:
    """Token counts of one generation."""

    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        """Prompt + completion tokens."""
        return self.prompt_tokens + self.completion_tokens


class AnswerGenerator(Protocol):
    """Streams the Answer JSON as text fragments; ``usage`` is filled once it ends."""

    model_name: str
    usage: Usage

    def stream(self, prompt: Prompt) -> AsyncIterator[str]:
        """Yield raw JSON fragments of the answer."""
        ...


class GeminiAnswerGenerator:
    """Gemini ``generate_content_stream`` with the Answer schema as structured output.

    Retries rate limits, server errors and timeouts, but only before the first chunk:
    after that the client already shows partial text.
    """

    def __init__(self, client: genai.Client | None = None, *, model: str | None = None) -> None:
        self._client = client or get_client()
        self.model_name = model or settings.GEMINI_MODEL
        self.usage = Usage()

    def _config(self, prompt: Prompt) -> types.GenerateContentConfig:
        """Build the request config for one prompt.

        Args:
            prompt: The rendered prompt.
        """
        return types.GenerateContentConfig(
            system_instruction=prompt.system,
            response_mime_type="application/json",
            response_schema=Answer,
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
        )

    async def _open(
        self, prompt: Prompt
    ) -> tuple[types.GenerateContentResponse, AsyncIterator[types.GenerateContentResponse]]:
        """Start the stream and read its first chunk, retrying retryable errors.

        Args:
            prompt: The rendered prompt.

        Returns:
            The first chunk and the rest of the stream.

        Raises:
            Exception: The last Gemini error when retries run out or it is not retryable.
        """
        attempts = settings.LLM_MAX_RETRIES + 1
        for attempt in range(1, attempts + 1):
            try:
                stream = await self._client.aio.models.generate_content_stream(
                    model=self.model_name, contents=prompt.user, config=self._config(prompt)
                )
                return await anext(stream), stream
            except Exception as exc:
                if attempt == attempts or not is_retryable(exc):
                    raise
                await asyncio.sleep(backoff_delay(attempt))
        raise AssertionError  # unreachable: the loop returns or raises

    def _record_usage(self, chunk: types.GenerateContentResponse) -> None:
        """Keep the latest token counts reported by Gemini.

        Args:
            chunk: A streamed response chunk.
        """
        metadata = chunk.usage_metadata
        if metadata is not None:
            self.usage = Usage(
                prompt_tokens=metadata.prompt_token_count or 0,
                completion_tokens=metadata.candidates_token_count or 0,
            )

    async def stream(self, prompt: Prompt) -> AsyncIterator[str]:
        """Yield the answer's JSON text as Gemini streams it.

        Args:
            prompt: The rendered prompt.
        """
        first, rest = await self._open(prompt)
        self._record_usage(first)
        if first.text:
            yield first.text
        async for chunk in rest:
            self._record_usage(chunk)
            if chunk.text:
                yield chunk.text


class FakeAnswerGenerator:
    """Yields a scripted answer in small fragments (tests, no network)."""

    model_name = "fake-generator"

    def __init__(
        self, answer_json: str, *, fragment_size: int = 16, usage: Usage | None = None
    ) -> None:
        self._answer_json = answer_json
        self._fragment_size = fragment_size
        self._final_usage = usage or Usage(prompt_tokens=100, completion_tokens=50)
        self.usage = Usage()
        self.prompts: list[Prompt] = []

    async def stream(self, prompt: Prompt) -> AsyncIterator[str]:
        """Yield the scripted JSON in fixed-size fragments and record the prompt.

        Args:
            prompt: The rendered prompt (kept for assertions).
        """
        self.prompts.append(prompt)
        for start in range(0, len(self._answer_json), self._fragment_size):
            yield self._answer_json[start : start + self._fragment_size]
        self.usage = self._final_usage
