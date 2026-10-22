"""Tests for SSE framing/keep-alive and the answer generators (no network)."""

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.genai import errors

from apps.chat.constants import PING
from apps.chat.generator import FakeAnswerGenerator, GeminiAnswerGenerator, Usage
from apps.chat.prompts import Prompt
from apps.chat.sse import Event, format_event, sse_stream

PROMPT = Prompt(system="rules", user="question", version="v1", sha256="0" * 64)


def test_format_event() -> None:
    """Events are framed as event/data lines with compact UTF-8 JSON."""
    assert format_event("delta", {"text": "oʻ"}) == 'event: delta\ndata: {"text":"oʻ"}\n\n'


async def _events(*names: str, pause: float = 0.0) -> AsyncGenerator[Event]:
    """Yield named events, optionally pausing before each."""
    for name in names:
        await asyncio.sleep(pause)
        yield Event(name)


async def _collect(stream: AsyncIterator[str]) -> list[str]:
    """Read a whole stream."""
    return [chunk async for chunk in stream]


async def test_stream_formats_events_in_order() -> None:
    """Events come out in order, framed."""
    chunks = await _collect(sse_stream(_events("meta", "done"), interval=1))
    assert chunks == [format_event("meta", {}), format_event("done", {})]


async def test_stream_pings_while_idle() -> None:
    """A slow producer gets ``: ping`` comments in between."""
    chunks = await _collect(sse_stream(_events("meta", pause=0.05), interval=0.01))
    assert PING in chunks
    assert chunks[-1] == format_event("meta", {})


async def test_disconnect_runs_generator_cleanup() -> None:
    """Closing the stream (client gone) closes the event generator, running its finally."""
    cleaned = asyncio.Event()

    async def slow() -> AsyncGenerator[Event]:
        """Yield one event, then wait forever; record cleanup."""
        try:
            yield Event("meta")
            await asyncio.sleep(3600)
            yield Event("never")
        finally:
            cleaned.set()

    stream: Any = sse_stream(slow(), interval=10)
    assert await anext(stream) == format_event("meta", {})
    await stream.aclose()
    assert cleaned.is_set()


async def test_generator_errors_propagate() -> None:
    """A crashing generator surfaces its error to the response."""

    async def boom(fail: bool) -> AsyncGenerator[Event]:
        """Fail before the first event when ``fail`` is set."""
        if fail:
            raise RuntimeError("boom")
        yield Event("never")

    with pytest.raises(RuntimeError, match="boom"):
        await _collect(sse_stream(boom(True), interval=1))


async def test_fake_generator_fragments_and_usage() -> None:
    """The fake yields the script in fragments and reports usage at the end."""
    fake = FakeAnswerGenerator('{"a": 1}', fragment_size=3, usage=Usage(5, 7))
    assert [f async for f in fake.stream(PROMPT)] == ['{"a', '": ', "1}"]
    assert fake.usage.total == 12
    assert fake.prompts == [PROMPT]


def _chunk(
    text: str | None, prompt_tokens: int = 10, completion: int = 4, thoughts: int = 0
) -> Any:
    """A fake Gemini stream chunk."""
    usage = SimpleNamespace(
        prompt_token_count=prompt_tokens,
        candidates_token_count=completion,
        thoughts_token_count=thoughts,
    )
    return SimpleNamespace(text=text, usage_metadata=usage)


async def _aiter(items: list[Any]) -> AsyncIterator[Any]:
    """Async iterator over ``items``."""
    for item in items:
        yield item


def _client(*responses: Any) -> MagicMock:
    """A fake genai client whose stream calls return/raise ``responses`` in turn."""
    client = MagicMock()
    client.aio.models.generate_content_stream = AsyncMock(side_effect=list(responses))
    return client


async def test_gemini_generator_streams_text_and_usage() -> None:
    """Text chunks are yielded; usage comes from the latest chunk; config uses the schema."""
    client = _client(_aiter([_chunk('{"a"'), _chunk(None), _chunk(":1}", 12, 9, thoughts=5)]))
    generator = GeminiAnswerGenerator(client, model="m")
    assert [t async for t in generator.stream(PROMPT)] == ['{"a"', ":1}"]
    assert (generator.usage.prompt_tokens, generator.usage.completion_tokens) == (12, 14)
    config = client.aio.models.generate_content_stream.call_args.kwargs["config"]
    assert config.response_mime_type == "application/json"
    assert config.system_instruction == "rules"
    assert "additionalProperties" not in str(config.response_schema)
    assert config.thinking_config.thinking_level == "LOW"


async def test_gemini_generator_retries_before_first_chunk() -> None:
    """A 503 on open is retried; a 400 is not."""
    unavailable = errors.APIError(503, {"error": {"message": "busy"}})
    client = _client(unavailable, _aiter([_chunk("{}")]))
    with patch("apps.chat.generator.asyncio.sleep", AsyncMock()):
        assert [t async for t in GeminiAnswerGenerator(client).stream(PROMPT)] == ["{}"]
    bad = errors.APIError(400, {"error": {"message": "bad"}})
    with pytest.raises(errors.APIError):
        _ = [t async for t in GeminiAnswerGenerator(_client(bad)).stream(PROMPT)]


async def test_gemini_generator_gives_up_after_retries() -> None:
    """Retryable errors stop after LLM_MAX_RETRIES + 1 attempts."""
    busy = errors.APIError(429, {"error": {"message": "slow down"}})
    client = _client(busy, busy, busy)
    with (
        patch("apps.chat.generator.asyncio.sleep", AsyncMock()),
        pytest.raises(errors.APIError),
    ):
        _ = [t async for t in GeminiAnswerGenerator(client).stream(PROMPT)]
    assert client.aio.models.generate_content_stream.await_count == 3
