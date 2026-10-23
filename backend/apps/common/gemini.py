"""The single place that builds Gemini clients, plus shared retry rules.

Only ``corpus/embeddings.py``, ``chat/generator.py`` and the collector extraction service
may use the client.
"""

import asyncio
import random
from collections.abc import Awaitable, Callable

import httpx
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from google import genai
from google.genai import errors, types

from apps.common.constants import (
    BACKOFF_BASE_S,
    BACKOFF_CAP_S,
    MS_PER_S,
    RETRY_INFO_CAP_S,
    RETRY_INFO_TYPE,
    RETRYABLE_STATUS,
)


def get_client() -> genai.Client:
    """Build a Gemini client (sync + ``.aio`` async).

    Not cached on purpose: the async client pools connections on the event loop that first
    used it, and workers run each task in a new loop (``async_to_sync``), so a shared client
    fails with "Event loop is closed". Callers keep one client per embedder/generator.

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


def server_retry_delay(exc: BaseException) -> float | None:
    """Seconds Gemini asks us to wait (``RetryInfo.retryDelay`` on a 429), or None.

    Args:
        exc: The error raised by a Gemini call.
    """
    details = getattr(exc, "details", None)
    if not isinstance(details, dict):
        return None
    for item in details.get("error", {}).get("details", []):
        delay = str(item.get("retryDelay", "")) if item.get("@type") == RETRY_INFO_TYPE else ""
        if delay.endswith("s"):
            try:
                return float(delay[:-1])
            except ValueError:
                return None
    return None


async def call_with_retries[T](
    call: Callable[[], Awaitable[T]], *, max_tries: int, honor_server_delay: bool = True
) -> T:
    """Run an async Gemini call, retrying retryable failures with backoff.

    Args:
        call: Zero-argument coroutine factory.
        max_tries: Total attempts, including the first.
        honor_server_delay: Wait Gemini's ``RetryInfo`` delay (off on latency-bound paths).

    Returns:
        The call's result.

    Rate limits wait what Gemini asks for (``RetryInfo``); a wait longer than
    ``RETRY_INFO_CAP_S`` (a daily quota) fails at once instead of retrying.

    Raises:
        Exception: The last error, when it is not retryable or tries run out.
    """
    for attempt in range(1, max_tries + 1):
        try:
            return await call()
        except Exception as exc:
            server_delay = server_retry_delay(exc) if honor_server_delay else None
            too_long = server_delay is not None and server_delay > RETRY_INFO_CAP_S
            if attempt == max_tries or not is_retryable(exc) or too_long:
                raise
            await asyncio.sleep(server_delay or backoff_delay(attempt))
    raise AssertionError  # unreachable: the loop returns or raises


async def aclose_client(client: genai.Client) -> None:
    """Close both halves of a Gemini client (async pool first, then the sync one).

    Each client owns httpx connection pools; closing them at the end of a request keeps
    long-running processes from leaking sockets.

    Args:
        client: A client from :func:`get_client`.
    """
    await client.aio.aclose()
    client.close()
