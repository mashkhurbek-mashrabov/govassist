"""The single place that builds Gemini clients, plus shared retry rules.

Only ``corpus/embeddings.py``, ``chat/generator.py`` and the collector extraction service
may use the client.
"""

import asyncio
import random
from collections.abc import Awaitable, Callable
from functools import cache

import httpx
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from google import genai
from google.genai import errors, types

RETRYABLE_STATUS = frozenset({408, 429, 500, 502, 503, 504})
BACKOFF_BASE_S = 0.5
BACKOFF_CAP_S = 20.0
MS_PER_S = 1000


@cache
def get_client() -> genai.Client:
    """Return the shared Gemini client (sync + ``.aio`` async).

    Raises:
        ImproperlyConfigured: When ``GEMINI_API_KEY`` is not set.
    """
    if not settings.GEMINI_API_KEY:
        msg = "GEMINI_API_KEY is not set."
        raise ImproperlyConfigured(msg)
    return genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=settings.LLM_TIMEOUT_S * MS_PER_S),
    )


def is_retryable(exc: BaseException) -> bool:
    """True for rate limits, server errors and timeouts.

    Args:
        exc: The error raised by a Gemini call.
    """
    if isinstance(exc, errors.APIError):
        return exc.code in RETRYABLE_STATUS
    return isinstance(exc, (httpx.TimeoutException, httpx.TransportError, TimeoutError))


def backoff_delay(attempt: int) -> float:
    """Exponential backoff with full jitter.

    Args:
        attempt: 1-based number of the failed attempt.

    Returns:
        Seconds to wait before the next attempt.
    """
    return random.uniform(0, min(BACKOFF_CAP_S, BACKOFF_BASE_S * 2**attempt))  # noqa: S311


async def call_with_retries[T](call: Callable[[], Awaitable[T]], *, max_tries: int) -> T:
    """Run an async Gemini call, retrying retryable failures with backoff.

    Args:
        call: Zero-argument coroutine factory.
        max_tries: Total attempts, including the first.

    Returns:
        The call's result.

    Raises:
        Exception: The last error, when it is not retryable or tries run out.
    """
    for attempt in range(1, max_tries + 1):
        try:
            return await call()
        except Exception as exc:
            if attempt == max_tries or not is_retryable(exc):
                raise
            await asyncio.sleep(backoff_delay(attempt))
    raise AssertionError  # unreachable: the loop returns or raises
