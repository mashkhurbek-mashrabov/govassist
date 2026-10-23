"""Generation ports: the streamed Answer JSON and the follow-up query rewrite (Gemini + fakes)."""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

from django.conf import settings
from google import genai
from google.genai import types

from apps.chat.constants import (
    REWRITE_MAX_OUTPUT_TOKENS,
    REWRITE_TEMPERATURE,
)
from apps.chat.prompts import Prompt
from apps.chat.schemas import gemini_response_schema
from apps.common.gemini import backoff_delay, get_client, is_retryable


@dataclass
class Usage:
    """Token counts of one generation; ``completion_tokens`` includes thinking tokens (billed)."""

    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        """Prompt + completion tokens."""
        return self.prompt_tokens + self.completion_tokens


def usage_of(response: types.GenerateContentResponse) -> Usage | None:
    """Token counts reported on a Gemini response (thinking tokens are billed as output).

    Args:
        response: A response or streamed chunk.
    """
    metadata = response.usage_metadata
    if metadata is None:
        return None
    output = (metadata.candidates_token_count or 0) + (metadata.thoughts_token_count or 0)
    return Usage(prompt_tokens=metadata.prompt_token_count or 0, completion_tokens=output)


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
            response_schema=gemini_response_schema(),
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
            thinking_config=types.ThinkingConfig(thinking_level=settings.LLM_THINKING_LEVEL),
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
        usage = usage_of(chunk)
        if usage is not None:
            self.usage = usage

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


class QueryRewriter(Protocol):
    """Rewrites a follow-up question into a standalone retrieval query (issue #34)."""

    model_name: str
    usage: Usage

    async def rewrite(self, prompt: Prompt) -> str:
        """Return the model's raw reply (cleaned by the caller)."""
        ...


class GeminiQueryRewriter:
    """One short, deterministic Gemini call; no retries (the caller falls back instead)."""

    def __init__(self, client: genai.Client | None = None, *, model: str | None = None) -> None:
        self._client = client or get_client()
        self.model_name = model or settings.GEMINI_MODEL
        self.usage = Usage()

    async def rewrite(self, prompt: Prompt) -> str:
        """Ask for the standalone query.

        Args:
            prompt: The rendered ``rewrite-v1`` prompt.

        Raises:
            Exception: Any Gemini error (the caller falls back to the original question).
        """
        response = await self._client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt.user,
            config=types.GenerateContentConfig(
                system_instruction=prompt.system,
                temperature=REWRITE_TEMPERATURE,
                max_output_tokens=REWRITE_MAX_OUTPUT_TOKENS,
                thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
            ),
        )
        self.usage = usage_of(response) or Usage()
        return response.text or ""


class FakeQueryRewriter:
    """Returns a scripted reply or raises a scripted error (tests, no network)."""

    model_name = "fake-rewriter"

    def __init__(self, reply: str | Exception, *, usage: Usage | None = None) -> None:
        self._reply = reply
        self._usage = usage or Usage(prompt_tokens=20, completion_tokens=5)
        self.usage = Usage()
        self.prompts: list[Prompt] = []

    async def rewrite(self, prompt: Prompt) -> str:
        """Record the prompt and return (or raise) the scripted reply.

        Args:
            prompt: The rendered prompt (kept for assertions).

        Raises:
            Exception: The scripted error, when one was given.
        """
        self.prompts.append(prompt)
        if isinstance(self._reply, Exception):
            raise self._reply
        self.usage = self._usage
        return self._reply
