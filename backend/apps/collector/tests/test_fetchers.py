"""Tests for crawler fetchers, robots policy, and rate limiting."""

import email.utils
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from apps.collector.fetchers import (
    DEFAULT_RETRY_BACKOFF_S,
    RETRY_AFTER_CAP_S,
    BrowserFetcher,
    FetchResult,
    HostRateLimiter,
    HttpFetcher,
    RobotsPolicy,
    parse_retry_after,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
NAMUNA_ROBOTS_TXT = (FIXTURES_DIR / "namuna_robots.txt").read_text(encoding="utf-8")
NAMUNA_URL = "https://example.uz/page"
NAMUNA_HOST = "example.uz"


def test_parse_retry_after_delta_seconds() -> None:
    """Verifies parsing of numeric Retry-After seconds capped at RETRY_AFTER_CAP_S."""
    assert parse_retry_after("10") == 10.0
    assert parse_retry_after("500") == RETRY_AFTER_CAP_S
    assert parse_retry_after(None) == DEFAULT_RETRY_BACKOFF_S
    assert parse_retry_after("not-a-number-or-date") == DEFAULT_RETRY_BACKOFF_S


def test_parse_retry_after_http_date() -> None:
    """Verifies parsing of HTTP IMF-fixdate format."""
    future = datetime.now(UTC) + timedelta(seconds=25)
    formatted_date = email.utils.format_datetime(future)
    delay = parse_retry_after(formatted_date)
    assert 20.0 <= delay <= 30.0


def test_host_rate_limiter_throttles() -> None:
    """Verifies rate limiter calls sleep with the remainder interval."""
    current_time = 100.0

    def mock_clock() -> float:
        return current_time

    sleep_calls: list[float] = []

    def mock_sleep(duration: float) -> None:
        nonlocal current_time
        sleep_calls.append(duration)
        current_time += duration

    limiter = HostRateLimiter(rate_per_host=2.0, clock=mock_clock, sleep=mock_sleep)
    # First request: immediate
    limiter.wait("https://example.uz/first")
    assert sleep_calls == []

    # Second request to same host immediately: waits 0.5s
    limiter.wait("https://example.uz/second")
    assert len(sleep_calls) == 1
    assert sleep_calls[0] == pytest.approx(0.5)

    # Request to a different host: immediate
    limiter.wait("https://other.uz/third")
    assert len(sleep_calls) == 1


def test_robots_policy_standard_allow_disallow() -> None:
    """Verifies robots.txt parsing and allow/disallow decisions."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=NAMUNA_ROBOTS_TXT)
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    policy = RobotsPolicy(client=client)

    assert policy.allowed("https://example.uz/public/page") is True
    assert policy.allowed("https://example.uz/admin/dashboard") is False
    assert policy.allowed("https://example.uz/private/data") is False
    assert policy.can_fetch("https://example.uz/allowed") is True


def test_robots_policy_4xx_allows() -> None:
    """Verifies 4xx robots.txt allows crawling."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    policy = RobotsPolicy(client=client)
    assert policy.allowed("https://example.uz/any-path") is True


def test_robots_policy_5xx_disallows() -> None:
    """Verifies 5xx robots.txt disallows crawling."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    policy = RobotsPolicy(client=client)
    assert policy.allowed("https://example.uz/any-path") is False


def test_robots_policy_unreachable_allows() -> None:
    """Verifies network transport errors allow crawling."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    policy = RobotsPolicy(client=client)
    assert policy.allowed("https://unreachable.uz/any-path") is True


def test_http_fetcher_success() -> None:
    """Verifies successful GET response."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html; charset=utf-8"},
            content=b"<html>NAMUNA</html>",
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = HttpFetcher(client=client)
    result = fetcher.fetch("https://example.uz/test")

    assert result.status == 200
    assert result.content_type == "text/html"
    assert result.body == b"<html>NAMUNA</html>"
    assert result.url == "https://example.uz/test"
    assert result.final_url == "https://example.uz/test"


def test_http_fetcher_retry_on_429() -> None:
    """Verifies 429 response triggers retry-after delay and retries."""
    attempts = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"Retry-After": "2"})
        return httpx.Response(200, headers={"Content-Type": "text/html"}, content=b"OK")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = HttpFetcher(client=client, sleep=sleeps.append)
    result = fetcher.fetch("https://example.uz/throttled")

    assert attempts == 2
    assert sleeps == [2.0]
    assert result.status == 200
    assert result.body == b"OK"


def test_http_fetcher_exhausts_retries() -> None:
    """Verifies 503 response returns after max retry attempts."""
    attempts = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, headers={"Retry-After": "1"}, content=b"Down")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = HttpFetcher(client=client, sleep=sleeps.append, max_attempts=3)
    result = fetcher.fetch("https://example.uz/unavailable")

    assert attempts == 3
    assert len(sleeps) == 2
    assert result.status == 503
    assert result.body == b"Down"


def test_http_fetcher_context_manager() -> None:
    """Verifies HttpFetcher supports context manager protocol."""
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200)))
    with HttpFetcher(client=client) as fetcher:
        assert isinstance(fetcher, HttpFetcher)


def test_browser_fetcher_with_mock_driver() -> None:
    """Verifies BrowserFetcher launches browser, visits URL, and returns HTML body."""
    mock_page = MagicMock()
    mock_page.goto.return_value = MagicMock(status=200)
    mock_page.url = "https://example.uz/final"
    mock_page.content.return_value = "<html><body>NAMUNA rendered</body></html>"

    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page

    mock_chromium = MagicMock()
    mock_chromium.launch.return_value = mock_browser

    mock_driver = MagicMock()
    mock_driver.chromium = mock_chromium

    fetcher = BrowserFetcher(playwright_driver=mock_driver)
    res: FetchResult = fetcher.fetch("https://example.uz/js-page")

    assert res.status == 200
    assert res.final_url == "https://example.uz/final"
    assert res.content_type == "text/html"
    assert b"NAMUNA rendered" in res.body
    mock_browser.close.assert_called_once()
