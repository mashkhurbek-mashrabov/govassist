"""Polite fetching: robots.txt, per-host rate limit, Retry-After, HTTP and browser fetchers."""

import email.utils
import logging
import time
import urllib.parse
import urllib.robotparser
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx
from django.conf import settings

from apps.collector.constants import (
    HTTP_CLIENT_ERROR,
    HTTP_SERVER_ERROR,
    PDF_TYPE,
    RETRY_AFTER_CAP_S,
    RETRY_FALLBACK_S,
    RETRY_MAX_ATTEMPTS,
)
from apps.common.constants import MS_PER_S, RETRYABLE_STATUS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FetchResult:
    """One fetched URL."""

    url: str
    final_url: str
    status: int
    content_type: str
    body: bytes

    @property
    def is_pdf(self) -> bool:
        """True when the response is a PDF (by type or file extension)."""
        return self.content_type == PDF_TYPE or self.final_url.lower().endswith(".pdf")


class Fetcher(Protocol):
    """Fetches one URL (``HttpFetcher`` or ``BrowserFetcher``)."""

    def fetch(self, url: str) -> FetchResult:
        """Fetch ``url``."""
        ...


def host_of(url: str) -> str:
    """Lowercased ``host[:port]`` of a URL.

    Args:
        url: Any absolute URL.
    """
    return urllib.parse.urlsplit(url).netloc.lower()


def build_client() -> httpx.Client:
    """An httpx client with the crawler's honest User-Agent and timeout."""
    return httpx.Client(
        headers={"User-Agent": settings.CRAWLER_USER_AGENT},
        timeout=settings.CRAWLER_TIMEOUT_S,
        follow_redirects=True,
    )


def parse_retry_after(value: str | None) -> float:
    """Seconds to wait from a ``Retry-After`` header (delta-seconds or HTTP date), capped.

    Args:
        value: The raw header, if any.
    """
    if not value:
        return RETRY_FALLBACK_S
    try:
        seconds = float(value)
    except ValueError:
        try:
            seconds = (email.utils.parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()
        except TypeError, ValueError:
            return RETRY_FALLBACK_S
    return max(0.0, min(seconds, RETRY_AFTER_CAP_S))


class HostRateLimiter:
    """Allows at most ``CRAWLER_RATE_PER_HOST`` requests per second to each host."""

    def __init__(
        self,
        rate_per_host: float | None = None,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        rate = rate_per_host if rate_per_host is not None else settings.CRAWLER_RATE_PER_HOST
        self._interval = 1.0 / rate if rate > 0 else 0.0
        self._clock = clock
        self._sleep = sleep
        self._last: dict[str, float] = {}

    def wait(self, url: str) -> None:
        """Sleep until a request to ``url``'s host is allowed, then record it.

        Args:
            url: The URL about to be fetched.
        """
        host = host_of(url)
        if host in self._last:
            remaining = self._interval - (self._clock() - self._last[host])
            if remaining > 0:
                self._sleep(remaining)
        self._last[host] = self._clock()


class RobotsPolicy:
    """robots.txt per host, fetched once with the crawler's User-Agent.

    Missing robots.txt (4xx) or an unreachable host allow crawling; a 5xx disallows it.
    """

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or build_client()
        self._rules: dict[str, urllib.robotparser.RobotFileParser | bool] = {}

    def _load(self, url: str) -> urllib.robotparser.RobotFileParser | bool:
        """Fetch and parse the robots.txt for ``url``'s host."""
        parts = urllib.parse.urlsplit(url)
        try:
            response = self._client.get(f"{parts.scheme}://{parts.netloc}/robots.txt")
        except httpx.TransportError:
            logger.warning("robots.txt unreachable, allowing", extra={"host": parts.netloc})
            return True
        if response.status_code >= HTTP_SERVER_ERROR:
            return False
        if response.status_code >= HTTP_CLIENT_ERROR:
            return True
        parser = urllib.robotparser.RobotFileParser()
        parser.parse(response.text.splitlines())
        return parser

    def allowed(self, url: str) -> bool:
        """True when robots.txt lets the crawler fetch ``url``.

        Args:
            url: The candidate URL.
        """
        host = host_of(url)
        if host not in self._rules:
            self._rules[host] = self._load(url)
        rules = self._rules[host]
        if isinstance(rules, bool):
            return rules
        return rules.can_fetch(settings.CRAWLER_USER_AGENT, url)


def _result(url: str, response: httpx.Response) -> FetchResult:
    """Wrap an httpx response."""
    content_type = response.headers.get("content-type", "application/octet-stream")
    return FetchResult(
        url=url,
        final_url=str(response.url),
        status=response.status_code,
        content_type=content_type.split(";")[0].strip().lower(),
        body=response.content,
    )


class HttpFetcher:
    """httpx fetcher; waits out 429/503 ``Retry-After`` a bounded number of times."""

    def __init__(
        self,
        client: httpx.Client | None = None,
        *,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = RETRY_MAX_ATTEMPTS,
    ) -> None:
        self._client = client or build_client()
        self._sleep = sleep
        self._max_attempts = max_attempts

    def _get(self, url: str) -> httpx.Response:
        """GET with bounded retries on transport errors (some hosts have flaky TLS nodes).

        Raises:
            httpx.TransportError: When every attempt fails.
        """
        for attempt in range(1, self._max_attempts + 1):
            try:
                return self._client.get(url)
            except httpx.TransportError:
                if attempt == self._max_attempts:
                    raise
                logger.warning("Transport error, retrying", extra={"url": url, "try": attempt})
                self._sleep(RETRY_FALLBACK_S)
        raise AssertionError  # unreachable: the loop returns or raises

    def fetch(self, url: str) -> FetchResult:
        """GET ``url``; the last response is returned even when it is an error.

        Args:
            url: The URL.
        """
        response = self._get(url)
        for attempt in range(1, self._max_attempts):
            if response.status_code not in RETRYABLE_STATUS:
                break
            wait = parse_retry_after(response.headers.get("Retry-After"))
            logger.warning(
                "Host asked us to wait",
                extra={"url": url, "status": response.status_code, "wait_s": wait, "try": attempt},
            )
            self._sleep(wait)
            response = self._get(url)
        return _result(url, response)


class BrowserFetcher:
    """Headless Chromium (Playwright) for JavaScript-rendered pages; worker image only."""

    def __init__(self, playwright_factory: Callable[[], Any] | None = None) -> None:
        self._playwright_factory = playwright_factory

    def _playwright(self) -> Any:
        """The Playwright context manager (imported lazily: not in the runtime image)."""
        if self._playwright_factory is not None:
            return self._playwright_factory()
        from playwright.sync_api import sync_playwright  # noqa: PLC0415

        return sync_playwright()

    def fetch(self, url: str) -> FetchResult:
        """Render ``url`` and return the resulting HTML.

        Args:
            url: The URL.
        """
        with self._playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=settings.CRAWLER_USER_AGENT)
                response = page.goto(url, timeout=settings.CRAWLER_TIMEOUT_S * MS_PER_S)
                return FetchResult(
                    url=url,
                    final_url=page.url,
                    status=response.status if response is not None else HTTP_CLIENT_ERROR,
                    content_type="text/html",
                    body=page.content().encode("utf-8"),
                )
            finally:
                browser.close()
