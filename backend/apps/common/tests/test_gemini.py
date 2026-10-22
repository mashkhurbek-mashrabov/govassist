"""Tests for the Gemini client factory and retry utilities."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from google.genai import errors

from apps.common.constants import BACKOFF_BASE_S, BACKOFF_CAP_S
from apps.common.gemini import backoff_delay, call_with_retries, get_client, is_retryable


def _api_error(code: int) -> errors.APIError:
    """Create a ``google.genai.errors.APIError`` with the given status code.

    Args:
        code: HTTP status code.
    """
    return errors.APIError(code=code, response_json={}, response=None)


# ---------------------------------------------------------------------------
# is_retryable
# ---------------------------------------------------------------------------


class TestIsRetryable:
    """Tests for ``is_retryable``."""

    def test_api_error_429_retryable(self) -> None:
        """HTTP 429 (rate limit) is retryable."""
        assert is_retryable(_api_error(429)) is True

    def test_api_error_500_retryable(self) -> None:
        """HTTP 500 (server error) is retryable."""
        assert is_retryable(_api_error(500)) is True

    def test_api_error_400_not_retryable(self) -> None:
        """HTTP 400 (bad request) is not retryable."""
        assert is_retryable(_api_error(400)) is False

    def test_httpx_read_timeout_retryable(self) -> None:
        """An ``httpx.ReadTimeout`` is retryable."""
        assert is_retryable(httpx.ReadTimeout("timeout")) is True

    def test_value_error_not_retryable(self) -> None:
        """A ``ValueError`` is not retryable."""
        assert is_retryable(ValueError("bad value")) is False

    def test_timeout_error_retryable(self) -> None:
        """A built-in ``TimeoutError`` is retryable."""
        assert is_retryable(TimeoutError()) is True

    def test_httpx_transport_error_retryable(self) -> None:
        """An ``httpx.TransportError`` is retryable."""
        assert is_retryable(httpx.ConnectError("conn refused")) is True


# ---------------------------------------------------------------------------
# backoff_delay
# ---------------------------------------------------------------------------


class TestBackoffDelay:
    """Tests for ``backoff_delay``."""

    def test_first_attempt_bounded(self) -> None:
        """First attempt delay is between 0 and ``BACKOFF_BASE_S * 2``."""
        for _ in range(100):
            delay = backoff_delay(1)
            assert 0 <= delay <= BACKOFF_BASE_S * 2

    def test_large_attempt_capped(self) -> None:
        """Very large attempts are capped at ``BACKOFF_CAP_S``."""
        for _ in range(100):
            delay = backoff_delay(20)
            assert 0 <= delay <= BACKOFF_CAP_S

    def test_delay_is_non_negative(self) -> None:
        """Every delay is non-negative."""
        for attempt in range(1, 10):
            assert backoff_delay(attempt) >= 0


# ---------------------------------------------------------------------------
# call_with_retries
# ---------------------------------------------------------------------------


class TestCallWithRetries:
    """Tests for ``call_with_retries``."""

    @pytest.mark.asyncio
    async def test_success_after_retries(self) -> None:
        """Retries on a retryable error and returns the successful result."""
        call = AsyncMock(side_effect=[_api_error(429), "success"])
        with patch("apps.common.gemini.asyncio.sleep", new_callable=AsyncMock):
            result = await call_with_retries(call, max_tries=3)
        assert result == "success"
        assert call.call_count == 2

    @pytest.mark.asyncio
    async def test_gives_up_after_max_tries(self) -> None:
        """Raises the last error when retries are exhausted."""
        call = AsyncMock(side_effect=_api_error(500))
        with (
            patch("apps.common.gemini.asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(errors.APIError),
        ):
            await call_with_retries(call, max_tries=3)
        assert call.call_count == 3

    @pytest.mark.asyncio
    async def test_does_not_retry_non_retryable(self) -> None:
        """A non-retryable error is raised immediately without retrying."""
        call = AsyncMock(side_effect=ValueError("bad value"))
        with pytest.raises(ValueError, match="bad value"):
            await call_with_retries(call, max_tries=3)
        assert call.call_count == 1

    @pytest.mark.asyncio
    async def test_sleep_called_between_retries(self) -> None:
        """``asyncio.sleep`` is called between retries."""
        call = AsyncMock(side_effect=[_api_error(429), "ok"])
        mock_sleep = AsyncMock()
        with patch("apps.common.gemini.asyncio.sleep", mock_sleep):
            await call_with_retries(call, max_tries=3)
        mock_sleep.assert_called_once()


# ---------------------------------------------------------------------------
# get_client
# ---------------------------------------------------------------------------


class TestGetClient:
    """Tests for ``get_client``."""

    def test_raises_when_api_key_empty(self) -> None:
        """Raises ``ImproperlyConfigured`` when ``GEMINI_API_KEY`` is empty."""
        with (
            override_settings(GEMINI_API_KEY=""),
            pytest.raises(ImproperlyConfigured, match="GEMINI_API_KEY"),
        ):
            get_client()

    def test_returns_client_when_key_set(self) -> None:
        """Returns a Gemini client when the API key is set."""
        with override_settings(GEMINI_API_KEY="test-fake-key-SAMPLE"):
            client = get_client()
            assert client is not None


class TestServerRetryDelay:
    """Tests for honouring Gemini's RetryInfo on 429s."""

    def _error(self, delay: str) -> errors.APIError:
        """A 429 carrying a RetryInfo detail."""
        details = {
            "error": {
                "code": 429,
                "details": [
                    {"@type": "type.googleapis.com/google.rpc.QuotaFailure"},
                    {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": delay},
                ],
            }
        }
        return errors.APIError(code=429, response_json=details, response=None)

    def test_delay_is_read_and_capped(self) -> None:
        """'37s' is 37 seconds; junk is ignored."""
        from apps.common.gemini import server_retry_delay  # noqa: PLC0415

        assert server_retry_delay(self._error("37s")) == 37.0
        assert server_retry_delay(self._error("soon")) is None
        assert server_retry_delay(ValueError()) is None

    async def test_call_with_retries_sleeps_the_server_delay(self) -> None:
        """The retry waits what the server asked for."""
        from unittest.mock import AsyncMock, patch  # noqa: PLC0415

        from apps.common.gemini import call_with_retries  # noqa: PLC0415

        call = AsyncMock(side_effect=[self._error("12s"), "ok"])
        with patch("apps.common.gemini.asyncio.sleep", AsyncMock()) as sleep:
            assert await call_with_retries(call, max_tries=2) == "ok"
        sleep.assert_awaited_once_with(12.0)

    async def test_daily_quota_is_not_retried(self) -> None:
        """A wait beyond the cap (daily quota) raises immediately."""
        from unittest.mock import AsyncMock  # noqa: PLC0415

        from apps.common.gemini import call_with_retries  # noqa: PLC0415

        call = AsyncMock(side_effect=self._error("73610s"))
        with pytest.raises(errors.APIError):
            await call_with_retries(call, max_tries=5)
        assert call.await_count == 1

    async def test_latency_bound_calls_ignore_the_server_delay(self) -> None:
        """honor_server_delay=False backs off briefly instead of waiting RetryInfo."""
        from unittest.mock import AsyncMock, patch  # noqa: PLC0415

        from apps.common.gemini import BACKOFF_CAP_S, call_with_retries  # noqa: PLC0415

        call = AsyncMock(side_effect=[self._error("60s"), "ok"])
        with patch("apps.common.gemini.asyncio.sleep", AsyncMock()) as sleep:
            assert await call_with_retries(call, max_tries=2, honor_server_delay=False) == "ok"
        assert sleep.await_args.args[0] <= BACKOFF_CAP_S
