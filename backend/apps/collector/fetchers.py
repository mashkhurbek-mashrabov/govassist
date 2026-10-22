"""Polite fetching: robots.txt, per-host rate limit, Retry-After, HTTP and browser fetchers."""

import email.utils
import ipaddress
import logging
import socket
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
    ALLOWED_SCHEMES,
    CRAWLER_MAX_BYTES,
    CRAWLER_MAX_REDIRECTS,
    CRAWLER_RETRY_STATUS,
    HTTP_CLIENT_ERROR,
    HTTP_SERVER_ERROR,
    PDF_TYPE,
    REDIRECT_STATUS,
    RETRY_AFTER_CAP_S,
    RETRY_FALLBACK_S,
    RETRY_MAX_ATTEMPTS,
)
from apps.common.constants import MS_PER_S

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
    """An httpx client with the crawler's honest User-Agent and timeout.

    Redirects are never followed automatically: every hop is checked by a ``UrlGuard``.
    """
    return httpx.Client(
        headers={"User-Agent": settings.CRAWLER_USER_AGENT},
        timeout=settings.CRAWLER_TIMEOUT_S,
        follow_redirects=False,
    )


class BlockedUrlError(Exception):
    """A URL the crawler must not fetch (scheme, host, private address, robots, size)."""


type Resolver = Callable[[str], list[str]]


def resolve_host(host: str) -> list[str]:
    """All IP addresses a host name resolves to.

    Raises:
        BlockedUrlError: When the name does not resolve.
    """
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        msg = f"{host} does not resolve"
        raise BlockedUrlError(msg) from exc
    return sorted({str(info[4][0]) for info in infos})


class UrlGuard:
    """SSRF guard checked on every URL and redirect hop.

    A URL passes when its scheme is http(s), its host is the source host or in
    ``CRAWLER_EXTRA_HOSTS``, every address it resolves to is public, and robots.txt allows it.
    """

    def __init__(
        self,
        allowed_hosts: set[str],
        robots: RobotsPolicy | None = None,
        resolver: Resolver = resolve_host,
    ) -> None:
        self._hosts = {host.lower() for host in allowed_hosts} | {
            host.lower() for host in settings.CRAWLER_EXTRA_HOSTS
        }
        self._robots = robots or RobotsPolicy()
        self._resolve = resolver

    def check(self, url: str) -> None:
        """Raise unless ``url`` may be fetched.

        Args:
            url: The URL about to be requested.

        Raises:
            BlockedUrlError: With the reason.
        """
        parts = urllib.parse.urlsplit(url)
        if parts.scheme not in ALLOWED_SCHEMES:
            msg = f"scheme {parts.scheme!r} not allowed"
            raise BlockedUrlError(msg)
        host = (parts.hostname or "").lower()
        if host_of(url) not in self._hosts and host not in self._hosts:
            msg = f"host {host!r} not allowed"
            raise BlockedUrlError(msg)
        for address in self._resolve(host):
            if not ipaddress.ip_address(address).is_global:
                msg = f"{host} resolves to non-public {address}"
                raise BlockedUrlError(msg)
        if not self._robots.allowed(url):
            msg = "disallowed by robots.txt"
            raise BlockedUrlError(msg)


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
        if response.status_code >= HTTP_CLIENT_ERROR or response.status_code in REDIRECT_STATUS:
            return True  # missing (or redirected) robots.txt: crawling allowed
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


def _read_capped(response: httpx.Response, url: str) -> bytes:
    """Read a streamed body, refusing anything over ``CRAWLER_MAX_BYTES``.

    Raises:
        BlockedUrlError: When the body is too large.
    """
    declared = response.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > CRAWLER_MAX_BYTES:
        msg = f"{url} declares {declared} bytes"
        raise BlockedUrlError(msg)
    body = bytearray()
    for chunk in response.iter_bytes():
        body += chunk
        if len(body) > CRAWLER_MAX_BYTES:
            msg = f"{url} is larger than {CRAWLER_MAX_BYTES} bytes"
            raise BlockedUrlError(msg)
    return bytes(body)


@dataclass(frozen=True)
class _Reply:
    """One HTTP exchange, already read (redirect target or capped body)."""

    status: int
    url: str
    headers: httpx.Headers
    body: bytes


class HttpFetcher:
    """httpx fetcher with an SSRF guard on every hop, a body cap and polite retries.

    Redirects are followed by hand (at most ``CRAWLER_MAX_REDIRECTS``), each hop checked by the
    guard. 429/503 ``Retry-After`` is waited out a bounded number of times.
    """

    def __init__(
        self,
        guard: UrlGuard,
        client: httpx.Client | None = None,
        *,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = RETRY_MAX_ATTEMPTS,
    ) -> None:
        self._guard = guard
        self._client = client or build_client()
        self._sleep = sleep
        self._max_attempts = max_attempts

    def _exchange(self, url: str) -> _Reply:
        """One guarded GET; retries transport errors (flaky TLS nodes) a bounded number of times.

        Raises:
            BlockedUrlError: When the guard or the size cap refuses.
            httpx.TransportError: When every attempt fails.
        """
        self._guard.check(url)
        for attempt in range(1, self._max_attempts + 1):
            try:
                with self._client.stream("GET", url) as response:
                    redirect = response.status_code in REDIRECT_STATUS
                    body = b"" if redirect else _read_capped(response, url)
                    return _Reply(response.status_code, str(response.url), response.headers, body)
            except httpx.TransportError:
                if attempt == self._max_attempts:
                    raise
                logger.warning("Transport error, retrying", extra={"url": url, "try": attempt})
                self._sleep(RETRY_FALLBACK_S)
        raise AssertionError  # unreachable: the loop returns or raises

    def _follow(self, url: str) -> _Reply:
        """GET with manual, guarded redirects.

        Raises:
            BlockedUrlError: On too many redirects or a refused hop.
        """
        reply = self._exchange(url)
        for _ in range(CRAWLER_MAX_REDIRECTS):
            if reply.status not in REDIRECT_STATUS:
                return reply
            target = urllib.parse.urljoin(reply.url, reply.headers.get("location", ""))
            reply = self._exchange(target)
        if reply.status in REDIRECT_STATUS:
            msg = f"more than {CRAWLER_MAX_REDIRECTS} redirects from {url}"
            raise BlockedUrlError(msg)
        return reply

    def fetch(self, url: str) -> FetchResult:
        """GET ``url``; the last response is returned even when it is an error.

        Args:
            url: The URL.

        Raises:
            BlockedUrlError: When any hop is refused or the body is too large.
        """
        reply = self._follow(url)
        for attempt in range(1, self._max_attempts):
            if reply.status not in CRAWLER_RETRY_STATUS:
                break
            wait = parse_retry_after(reply.headers.get("Retry-After"))
            logger.warning(
                "Host asked us to wait",
                extra={"url": url, "status": reply.status, "wait_s": wait, "try": attempt},
            )
            self._sleep(wait)
            reply = self._follow(url)
        content_type = reply.headers.get("content-type", "application/octet-stream")
        return FetchResult(
            url=url,
            final_url=reply.url,
            status=reply.status,
            content_type=content_type.split(";")[0].strip().lower(),
            body=reply.body,
        )


class BrowserFetcher:
    """Headless Chromium (Playwright) for JavaScript-rendered pages; worker image only.

    The guard checks the start URL, every navigation request (refused ones are aborted) and
    the final URL after redirects; the rendered HTML is capped at ``CRAWLER_MAX_BYTES``.
    """

    def __init__(
        self, guard: UrlGuard, playwright_factory: Callable[[], Any] | None = None
    ) -> None:
        self._guard = guard
        self._playwright_factory = playwright_factory

    def _playwright(self) -> Any:
        """The Playwright context manager (imported lazily: not in the runtime image)."""
        if self._playwright_factory is not None:
            return self._playwright_factory()
        from playwright.sync_api import sync_playwright  # noqa: PLC0415

        return sync_playwright()

    def _route(self, route: Any) -> None:
        """Abort navigation requests the guard refuses; let page resources through."""
        request = route.request
        if request.is_navigation_request():
            try:
                self._guard.check(request.url)
            except BlockedUrlError:
                logger.warning("Blocked navigation", extra={"url": request.url})
                route.abort()
                return
        route.continue_()

    def fetch(self, url: str) -> FetchResult:
        """Render ``url`` and return the resulting HTML.

        Args:
            url: The URL.

        Raises:
            BlockedUrlError: When the start or final URL is refused or the HTML is too large.
        """
        self._guard.check(url)
        with self._playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=settings.CRAWLER_USER_AGENT)
                page.route("**/*", self._route)
                response = page.goto(url, timeout=settings.CRAWLER_TIMEOUT_S * MS_PER_S)
                self._guard.check(page.url)
                body = page.content().encode("utf-8")
                if len(body) > CRAWLER_MAX_BYTES:
                    msg = f"{url} rendered more than {CRAWLER_MAX_BYTES} bytes"
                    raise BlockedUrlError(msg)
                return FetchResult(
                    url=url,
                    final_url=page.url,
                    status=response.status if response is not None else HTTP_CLIENT_ERROR,
                    content_type="text/html",
                    body=body,
                )
            finally:
                browser.close()
