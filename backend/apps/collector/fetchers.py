"""HTTP and browser fetchers, rate limiting, and robots policy."""

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

logger = logging.getLogger(__name__)

RETRY_AFTER_CAP_S = 300.0
RETRY_MAX_ATTEMPTS = 3
DEFAULT_RETRY_BACKOFF_S = 1.0
DEFAULT_USER_AGENT = "GovAssistBot/1.0 (+https://govassist.uz/bot)"
DEFAULT_TIMEOUT_S = 30
DEFAULT_RATE_PER_HOST = 1.0
MS_PER_S = 1000
HTTP_CLIENT_ERROR_MIN = 400
HTTP_SERVER_ERROR_MIN = 500
HTTP_RETRYABLE_STATUS = frozenset({429, 503})


@dataclass(frozen=True)
class FetchResult:
    """Result of fetching a single URL."""

    url: str
    final_url: str
    status: int
    content_type: str
    body: bytes


class Fetcher(Protocol):
    """Protocol for fetching resources over HTTP or browser."""

    def fetch(self, url: str) -> FetchResult:
        """Fetch the page at the given URL.

        Args:
            url: The URL to fetch.

        Returns:
            FetchResult with status, headers, and body.
        """
        ...


def parse_retry_after(header_val: str | None, *, cap_s: float = RETRY_AFTER_CAP_S) -> float:
    """Parse a Retry-After header into seconds to wait, capped at cap_s.

    Args:
        header_val: Raw Retry-After header string (delta-seconds or IMF-fixdate).
        cap_s: Maximum delay permitted.

    Returns:
        Delay in seconds, bounded between 0 and cap_s.
    """
    if not header_val:
        return DEFAULT_RETRY_BACKOFF_S
    try:
        return max(0.0, min(float(header_val), cap_s))
    except ValueError:
        pass

    try:
        parsed_dt = email.utils.parsedate_to_datetime(header_val)
        delta = (parsed_dt - datetime.now(UTC)).total_seconds()
        return max(0.0, min(delta, cap_s))
    except Exception:
        return DEFAULT_RETRY_BACKOFF_S


class HostRateLimiter:
    """Enforces a per-host request rate limit."""

    def __init__(
        self,
        rate_per_host: float | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Initialize with an optional rate and injectable clock/sleep.

        Args:
            rate_per_host: Max requests per second per host.
            clock: Monotonic clock provider.
            sleep: Sleep function.
        """
        rate = (
            rate_per_host
            if rate_per_host is not None
            else getattr(settings, "CRAWLER_RATE_PER_HOST", DEFAULT_RATE_PER_HOST)
        )
        self.min_interval = 1.0 / rate if rate > 0 else 0.0
        self.clock = clock
        self.sleep = sleep
        self._last_access: dict[str, float] = {}

    def wait(self, url: str) -> None:
        """Wait if needed before allowing a request to the host in url.

        Args:
            url: Target URL whose host rate is throttled.
        """
        host = urllib.parse.urlsplit(url).netloc.lower()
        now = self.clock()
        last = self._last_access.get(host, 0.0)
        elapsed = now - last
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            self.sleep(wait_time)
            self._last_access[host] = self.clock()
        else:
            self._last_access[host] = now


class RobotsPolicy:
    """Fetches and enforces robots.txt rules per host."""

    def __init__(
        self,
        user_agent: str | None = None,
        timeout_s: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        """Initialize robots policy.

        Args:
            user_agent: Crawler user agent to check against robots.txt.
            timeout_s: Fetch timeout in seconds.
            client: Optional HTTP client for robots.txt requests.
        """
        ua: str = (
            user_agent
            if user_agent is not None
            else str(getattr(settings, "CRAWLER_USER_AGENT", DEFAULT_USER_AGENT))
        )
        self.user_agent: str = ua
        self.timeout_s: float = (
            timeout_s
            if timeout_s is not None
            else float(getattr(settings, "CRAWLER_TIMEOUT_S", DEFAULT_TIMEOUT_S))
        )
        self._client = client
        self._cache: dict[str, bool | urllib.robotparser.RobotFileParser] = {}

    def _get_client(self) -> httpx.Client:
        """Return the active HTTP client or a new default client."""
        if self._client is not None:
            return self._client
        return httpx.Client(
            headers={"User-Agent": self.user_agent},
            timeout=self.timeout_s,
            follow_redirects=True,
        )

    def _load_host_rules(self, url: str) -> None:
        """Fetch and cache robots.txt for the host of the given URL.

        Rules:
          - Unreachable (connection/timeout error) -> allow (True)
          - 4xx -> allow (True)
          - 5xx -> disallow (False)
          - 200 -> parse RobotFileParser

        Args:
            url: URL from which host is extracted.
        """
        parsed = urllib.parse.urlsplit(url)
        host = parsed.netloc.lower()
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        client = self._get_client()
        owns_client = self._client is None
        try:
            resp = client.get(robots_url)
            if resp.status_code >= HTTP_SERVER_ERROR_MIN:
                self._cache[host] = False
            elif resp.status_code >= HTTP_CLIENT_ERROR_MIN:
                self._cache[host] = True
            else:
                rfp = urllib.robotparser.RobotFileParser()
                rfp.parse(resp.text.splitlines())
                self._cache[host] = rfp
        except httpx.TransportError, httpx.TimeoutException:
            self._cache[host] = True
        finally:
            if owns_client:
                client.close()

    def allowed(self, url: str) -> bool:
        """Check whether fetching the given URL is allowed by robots.txt.

        Args:
            url: Candidate URL to test.

        Returns:
            True if allowed, False if disallowed.
        """
        host = urllib.parse.urlsplit(url).netloc.lower()
        if host not in self._cache:
            self._load_host_rules(url)

        entry = self._cache.get(host)
        if isinstance(entry, bool):
            return entry
        if isinstance(entry, urllib.robotparser.RobotFileParser):
            return entry.can_fetch(self.user_agent, url)
        return True

    def can_fetch(self, url: str) -> bool:
        """Alias for ``allowed(url)``.

        Args:
            url: Candidate URL to test.

        Returns:
            True if allowed, False if disallowed.
        """
        return self.allowed(url)


class HttpFetcher:
    """HTTP fetcher with user agent, timeout, redirect following, and retry logic."""

    def __init__(
        self,
        client: httpx.Client | None = None,
        user_agent: str | None = None,
        timeout_s: float | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = RETRY_MAX_ATTEMPTS,
    ) -> None:
        """Initialize HttpFetcher.

        Args:
            client: Optional httpx.Client instance.
            user_agent: User-Agent string.
            timeout_s: Request timeout in seconds.
            sleep: Sleep function for retry backoff.
            max_attempts: Maximum retry attempts for 429/503.
        """
        ua: str = (
            user_agent
            if user_agent is not None
            else str(getattr(settings, "CRAWLER_USER_AGENT", DEFAULT_USER_AGENT))
        )
        self.user_agent: str = ua
        self.timeout_s: float = (
            timeout_s
            if timeout_s is not None
            else float(getattr(settings, "CRAWLER_TIMEOUT_S", DEFAULT_TIMEOUT_S))
        )
        self.sleep = sleep
        self.max_attempts = max_attempts
        self._owns_client = client is None
        self._client = client or httpx.Client(
            headers={"User-Agent": self.user_agent},
            timeout=self.timeout_s,
            follow_redirects=True,
        )

    def close(self) -> None:
        """Close the underlying client if owned."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> HttpFetcher:
        """Enter context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager and close client."""
        self.close()

    def fetch(self, url: str) -> FetchResult:
        """Fetch URL with retries on 429 and 503 with Retry-After.

        Args:
            url: Target URL.

        Returns:
            FetchResult with status, content_type, and body bytes.
        """
        for attempt in range(1, self.max_attempts + 1):
            resp = self._client.get(url)
            if resp.status_code in HTTP_RETRYABLE_STATUS and attempt < self.max_attempts:
                retry_after_str = resp.headers.get("Retry-After")
                wait_time = parse_retry_after(retry_after_str)
                logger.warning(
                    "HTTP %d on %s, attempt %d/%d. Waiting %.1fs.",
                    resp.status_code,
                    url,
                    attempt,
                    self.max_attempts,
                    wait_time,
                )
                self.sleep(wait_time)
                continue

            raw_content_type = resp.headers.get("content-type", "application/octet-stream")
            content_type = raw_content_type.split(";")[0].strip().lower()

            return FetchResult(
                url=url,
                final_url=str(resp.url),
                status=resp.status_code,
                content_type=content_type,
                body=resp.content,
            )

        # Fallback in case of loop termination without return
        raw_content_type = resp.headers.get("content-type", "application/octet-stream")
        content_type = raw_content_type.split(";")[0].strip().lower()
        return FetchResult(
            url=url,
            final_url=str(resp.url),
            status=resp.status_code,
            content_type=content_type,
            body=resp.content,
        )


class BrowserFetcher:
    """Fetcher using headless Playwright Chromium for JS-rendered pages."""

    def __init__(
        self,
        user_agent: str | None = None,
        timeout_s: float | None = None,
        playwright_driver: Any = None,
    ) -> None:
        """Initialize BrowserFetcher with lazy Playwright loading.

        Args:
            user_agent: User-Agent header for browser context.
            timeout_s: Navigation timeout in seconds.
            playwright_driver: Optional mock or injected playwright driver.
        """
        self.user_agent: str = (
            user_agent
            if user_agent is not None
            else str(getattr(settings, "CRAWLER_USER_AGENT", DEFAULT_USER_AGENT))
        )
        raw_timeout: float = (
            timeout_s
            if timeout_s is not None
            else float(getattr(settings, "CRAWLER_TIMEOUT_S", DEFAULT_TIMEOUT_S))
        )
        self.timeout_ms = int(raw_timeout * MS_PER_S)
        self._driver = playwright_driver

    def fetch(self, url: str) -> FetchResult:
        """Render page in Chromium and return HTML bytes.

        Args:
            url: Target URL to load.

        Returns:
            FetchResult with rendered HTML.
        """
        if self._driver is not None:
            browser = self._driver.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=self.user_agent)
                resp = page.goto(url, timeout=self.timeout_ms)
                status = resp.status if resp is not None else 200
                final_url = page.url
                html_text = page.content()
                return FetchResult(
                    url=url,
                    final_url=final_url,
                    status=status,
                    content_type="text/html",
                    body=html_text.encode("utf-8"),
                )
            finally:
                browser.close()

        from playwright.sync_api import sync_playwright  # noqa: PLC0415

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=self.user_agent)
                resp = page.goto(url, timeout=self.timeout_ms)
                status = resp.status if resp is not None else 200
                final_url = page.url
                html_text = page.content()
                return FetchResult(
                    url=url,
                    final_url=final_url,
                    status=status,
                    content_type="text/html",
                    body=html_text.encode("utf-8"),
                )
            finally:
                browser.close()
