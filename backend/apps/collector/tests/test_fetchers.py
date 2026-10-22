"""Tests for robots.txt, rate limiting, Retry-After and the fetchers (httpx MockTransport)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from apps.collector.fetchers import (
    RETRY_AFTER_CAP_S,
    RETRY_FALLBACK_S,
    BrowserFetcher,
    HostRateLimiter,
    HttpFetcher,
    RobotsPolicy,
    parse_retry_after,
)

UA = "GovAssist-research/1.0 (+https://github.com/mashkhurbek-mashrabov/govassist)"


def _client(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.Client:
    """An httpx client served by ``handler``."""
    return httpx.Client(transport=httpx.MockTransport(handler), headers={"User-Agent": UA})


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, RETRY_FALLBACK_S),
        ("7", 7.0),
        ("-3", 0.0),
        ("99999", RETRY_AFTER_CAP_S),
        ("soon", RETRY_FALLBACK_S),
    ],
)
def test_parse_retry_after(value: str | None, expected: float) -> None:
    """Seconds, negatives, caps and junk."""
    assert parse_retry_after(value) == expected


def test_parse_retry_after_http_date() -> None:
    """An HTTP date in the future gives the remaining seconds."""
    when = format_datetime(datetime.now(UTC) + timedelta(seconds=60), usegmt=True)
    assert 50 < parse_retry_after(when) <= 60


def test_rate_limiter_spaces_requests_per_host() -> None:
    """The second request to a host waits; another host does not."""
    now = [100.0]
    slept: list[float] = []

    def sleep(seconds: float) -> None:
        """Advance the fake clock."""
        slept.append(seconds)
        now[0] += seconds

    limiter = HostRateLimiter(2.0, clock=lambda: now[0], sleep=sleep)
    limiter.wait("https://a.example/1")
    now[0] += 0.1
    limiter.wait("https://a.example/2")
    limiter.wait("https://b.example/1")
    assert slept == [pytest.approx(0.4)]


def _robots(status: int, body: str = "") -> RobotsPolicy:
    """A robots policy whose robots.txt answers ``status``."""
    return RobotsPolicy(_client(lambda request: httpx.Response(status, text=body)))


def test_robots_rules_are_applied_and_cached() -> None:
    """Disallowed paths are refused; robots.txt is fetched once per host."""
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        """Serve one robots.txt."""
        calls.append(str(request.url))
        return httpx.Response(200, text="User-agent: *\nDisallow: /login\n")

    robots = RobotsPolicy(_client(handler))
    assert robots.allowed("https://my.example/uz/service/1")
    assert not robots.allowed("https://my.example/login")
    assert calls == ["https://my.example/robots.txt"]


@pytest.mark.parametrize(("status", "allowed"), [(404, True), (503, False)])
def test_robots_status_rules(status: int, allowed: bool) -> None:
    """Missing robots.txt allows; a server error disallows."""
    assert _robots(status).allowed("https://x.example/a") is allowed


def test_robots_unreachable_allows() -> None:
    """A network error on robots.txt allows (logged)."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Fail like a dead host."""
        raise httpx.ConnectError("down")

    assert RobotsPolicy(_client(handler)).allowed("https://x.example/a")


def test_http_fetcher_waits_out_429_then_succeeds() -> None:
    """Retry-After is honoured and the final response is wrapped."""
    replies = iter(
        [
            httpx.Response(429, headers={"Retry-After": "2"}),
            httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, text="ok"),
        ]
    )
    slept: list[float] = []
    fetcher = HttpFetcher(_client(lambda request: next(replies)), sleep=slept.append)
    result = fetcher.fetch("https://x.example/a")
    assert (result.status, result.content_type, result.body) == (200, "text/html", b"ok")
    assert slept == [2.0]
    assert not result.is_pdf


def test_http_fetcher_gives_up_after_max_attempts() -> None:
    """A host that keeps saying 503 gets three tries, then the 503 is returned."""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        """Always busy."""
        calls.append(1)
        return httpx.Response(503)

    result = HttpFetcher(_client(handler), sleep=lambda s: None).fetch("https://x.example/a")
    assert result.status == 503
    assert len(calls) == 3


def test_browser_fetcher_renders_with_playwright() -> None:
    """The browser fetcher returns the rendered HTML and always closes the browser."""
    page = MagicMock(url="https://x.example/final", content=MagicMock(return_value="<p>hi</p>"))
    page.goto.return_value = SimpleNamespace(status=200)
    browser = MagicMock(new_page=MagicMock(return_value=page))
    playwright = MagicMock()
    playwright.__enter__.return_value.chromium.launch.return_value = browser

    def factory() -> Any:
        """Return the fake Playwright context manager."""
        return playwright

    result = BrowserFetcher(factory).fetch("https://x.example/a")
    assert (result.final_url, result.body, result.status) == (
        "https://x.example/final",
        b"<p>hi</p>",
        200,
    )
    assert browser.close.called
    assert browser.new_page.call_args.kwargs["user_agent"].startswith("GovAssist-research")
