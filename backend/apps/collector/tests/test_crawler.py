"""Unit tests for breadth-first web crawler engine."""

import re
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

import pytest

from apps.collector.crawler import crawl
from apps.collector.fetchers import FetchResult, HostRateLimiter
from apps.collector.models import CrawlJob, CrawlSource, RawPage
from apps.collector.pipelines import Pipeline
from apps.corpus.models import DocumentKind


class FakeFetcher:
    """Fake fetcher returning configured FetchResults or raising configured errors."""

    def __init__(self, responses: Mapping[str, FetchResult | Exception]) -> None:
        """Initialize FakeFetcher with response mapping.

        Args:
            responses: Map from URL to FetchResult or Exception.
        """
        self.responses = responses
        self.requested_urls: list[str] = []

    def fetch(self, url: str) -> FetchResult:
        """Fetch URL from canned responses.

        Args:
            url: Target URL.

        Returns:
            FetchResult if configured.

        Raises:
            Exception: If an exception is configured for this URL.
        """
        self.requested_urls.append(url)
        resp = self.responses.get(url)
        if resp is None:
            return FetchResult(
                url=url,
                final_url=url,
                status=404,
                content_type="text/html",
                body=b"<html><body>404 Not Found</body></html>",
            )
        if isinstance(resp, Exception):
            raise resp
        return resp


class FakeRobotsPolicy:
    """Fake robots policy allowing or disallowing specific URLs."""

    def __init__(self, disallowed_urls: set[str] | None = None) -> None:
        """Initialize with set of disallowed URLs.

        Args:
            disallowed_urls: URLs disallowed by policy.
        """
        self.disallowed_urls = disallowed_urls or set()

    def can_fetch(self, url: str) -> bool:
        """Check if URL is allowed.

        Args:
            url: Target URL.

        Returns:
            True if allowed, False otherwise.
        """
        return url not in self.disallowed_urls


class RecordingPipeline(Pipeline):
    """Pipeline that records calls for verification."""

    def __init__(self) -> None:
        """Initialize pipeline with empty call history."""
        self.processed_calls: list[tuple[CrawlSource, FetchResult, str, datetime]] = []

    def process(
        self,
        source: CrawlSource,
        page: FetchResult,
        *,
        url: str,
        fetched_at: datetime,
    ) -> None:
        """Record process call.

        Args:
            source: Source being crawled.
            page: Fetched page data.
            url: Canonical or final URL.
            fetched_at: Timestamp of fetch.
        """
        self.processed_calls.append((source, page, url, fetched_at))


def _make_limiter() -> HostRateLimiter:
    """Create a fast rate limiter that does not sleep."""
    return HostRateLimiter(rate_per_host=1000.0, sleep=lambda _d: None)


@pytest.mark.django_db
def test_crawler_bfs_and_max_pages() -> None:
    """Verifies crawler traverses links BFS and stops when max_pages is reached."""
    source = CrawlSource.objects.create(
        name="NAMUNA Sayt",
        start_url="https://example.uz",
        kind=CrawlSource.Kind.DOCUMENT,
        document_kind=DocumentKind.OTHER,
        publisher="namuna.uz",
        max_pages=2,
    )

    responses: dict[str, FetchResult | Exception] = {
        "https://example.uz": FetchResult(
            url="https://example.uz",
            final_url="https://example.uz",
            status=200,
            content_type="text/html",
            body=(
                b"<html><body>"
                b'<a href="/page1">1</a>'
                b'<a href="/page2">2</a>'
                b'<a href="/page3">3</a>'
                b"</body></html>"
            ),
        ),
        "https://example.uz/page1": FetchResult(
            url="https://example.uz/page1",
            final_url="https://example.uz/page1",
            status=200,
            content_type="text/html",
            body=b"<html><body><h1>Sahifa 1</h1></body></html>",
        ),
        "https://example.uz/page2": FetchResult(
            url="https://example.uz/page2",
            final_url="https://example.uz/page2",
            status=200,
            content_type="text/html",
            body=b"<html><body><h1>Sahifa 2</h1></body></html>",
        ),
    }

    fetcher = FakeFetcher(responses)
    pipeline = RecordingPipeline()
    limiter = _make_limiter()
    robots = FakeRobotsPolicy()

    job = crawl(source, fetcher=fetcher, robots=robots, limiter=limiter, pipeline=pipeline)

    assert job.status == CrawlJob.Status.DONE
    assert job.pages_fetched == 2
    assert job.pages_skipped == 0
    assert job.finished_at is not None
    source.refresh_from_db()
    assert source.last_crawled_at == job.finished_at

    # Only start page and page1 fetched due to max_pages=2
    assert fetcher.requested_urls == ["https://example.uz", "https://example.uz/page1"]
    assert len(pipeline.processed_calls) == 2

    # Verify RawPage rows
    raw_pages = list(RawPage.objects.filter(job=job).order_by("fetched_at"))
    assert len(raw_pages) == 2
    for rp in raw_pages:
        assert Path(rp.raw_path).exists()
        assert Path(rp.raw_path).suffix == ".html"


@pytest.mark.django_db
def test_crawler_skips_robots_disallowed() -> None:
    """Verifies crawler respects robots.txt disallow rules and increments skipped count."""
    source = CrawlSource.objects.create(
        name="NAMUNA Sayt",
        start_url="https://example.uz",
        kind=CrawlSource.Kind.DOCUMENT,
        publisher="namuna.uz",
        max_pages=5,
    )

    responses: dict[str, FetchResult | Exception] = {
        "https://example.uz": FetchResult(
            url="https://example.uz",
            final_url="https://example.uz",
            status=200,
            content_type="text/html",
            body=(
                b"<html><body>"
                b'<a href="/secret">Secret</a>'
                b'<a href="/public">Public</a>'
                b"</body></html>"
            ),
        ),
        "https://example.uz/public": FetchResult(
            url="https://example.uz/public",
            final_url="https://example.uz/public",
            status=200,
            content_type="text/html",
            body=b"<html><body>Public Page</body></html>",
        ),
    }

    fetcher = FakeFetcher(responses)
    pipeline = RecordingPipeline()
    limiter = _make_limiter()
    robots = FakeRobotsPolicy(disallowed_urls={"https://example.uz/secret"})

    job = crawl(source, fetcher=fetcher, robots=robots, limiter=limiter, pipeline=pipeline)

    assert job.status == CrawlJob.Status.DONE
    assert job.pages_fetched == 2
    assert job.pages_skipped == 1
    assert "https://example.uz/secret" not in fetcher.requested_urls


@pytest.mark.django_db
def test_crawler_skips_off_host_links() -> None:
    """Verifies crawler does not follow links pointing to external hostnames."""
    source = CrawlSource.objects.create(
        name="NAMUNA Sayt",
        start_url="https://example.uz",
        kind=CrawlSource.Kind.DOCUMENT,
        publisher="namuna.uz",
        max_pages=5,
    )

    responses: dict[str, FetchResult | Exception] = {
        "https://example.uz": FetchResult(
            url="https://example.uz",
            final_url="https://example.uz",
            status=200,
            content_type="text/html",
            body=b'<html><body><a href="https://external.uz/page">External</a></body></html>',
        ),
    }

    fetcher = FakeFetcher(responses)
    pipeline = RecordingPipeline()
    limiter = _make_limiter()
    robots = FakeRobotsPolicy()

    job = crawl(source, fetcher=fetcher, robots=robots, limiter=limiter, pipeline=pipeline)

    assert job.status == CrawlJob.Status.DONE
    assert job.pages_fetched == 1
    assert fetcher.requested_urls == ["https://example.uz"]


@pytest.mark.django_db
def test_crawler_allowed_url_pattern_filter() -> None:
    """Verifies crawler only follows links matching allowed_url_pattern regex."""
    source = CrawlSource.objects.create(
        name="NAMUNA Xizmatlar",
        start_url="https://example.uz",
        allowed_url_pattern=r"^https://example\.uz/service/\d+$",
        kind=CrawlSource.Kind.DOCUMENT,
        publisher="namuna.uz",
        max_pages=5,
    )

    responses: dict[str, FetchResult | Exception] = {
        "https://example.uz": FetchResult(
            url="https://example.uz",
            final_url="https://example.uz",
            status=200,
            content_type="text/html",
            body=(
                b"<html><body>"
                b'<a href="/service/123">Allowed</a>'
                b'<a href="/about">Not Allowed</a>'
                b"</body></html>"
            ),
        ),
        "https://example.uz/service/123": FetchResult(
            url="https://example.uz/service/123",
            final_url="https://example.uz/service/123",
            status=200,
            content_type="text/html",
            body=b"<html><body>Xizmat 123</body></html>",
        ),
        "https://example.uz/about": FetchResult(
            url="https://example.uz/about",
            final_url="https://example.uz/about",
            status=200,
            content_type="text/html",
            body=b"<html><body>About</body></html>",
        ),
    }

    fetcher = FakeFetcher(responses)
    pipeline = RecordingPipeline()
    limiter = _make_limiter()
    robots = FakeRobotsPolicy()

    job = crawl(source, fetcher=fetcher, robots=robots, limiter=limiter, pipeline=pipeline)

    assert job.status == CrawlJob.Status.DONE
    assert job.pages_fetched == 2
    assert fetcher.requested_urls == ["https://example.uz", "https://example.uz/service/123"]


@pytest.mark.django_db
def test_crawler_unchanged_content_skips_pipeline() -> None:
    """Verifies unchanged content hash creates RawPage but skips pipeline processing."""
    source = CrawlSource.objects.create(
        name="NAMUNA Sayt",
        start_url="https://example.uz",
        kind=CrawlSource.Kind.DOCUMENT,
        publisher="namuna.uz",
        max_pages=1,
    )

    page_body = b"<html><body>Doimiy sahifa mazmuni</body></html>"
    responses: dict[str, FetchResult | Exception] = {
        "https://example.uz": FetchResult(
            url="https://example.uz",
            final_url="https://example.uz",
            status=200,
            content_type="text/html",
            body=page_body,
        ),
    }

    fetcher = FakeFetcher(responses)
    pipeline = RecordingPipeline()
    limiter = _make_limiter()
    robots = FakeRobotsPolicy()

    # First crawl
    job1 = crawl(source, fetcher=fetcher, robots=robots, limiter=limiter, pipeline=pipeline)
    assert job1.status == CrawlJob.Status.DONE
    assert len(pipeline.processed_calls) == 1

    # Second crawl with same content
    pipeline.processed_calls.clear()
    job2 = crawl(source, fetcher=fetcher, robots=robots, limiter=limiter, pipeline=pipeline)
    assert job2.status == CrawlJob.Status.DONE
    assert job2.pages_fetched == 1
    # Pipeline was skipped!
    assert len(pipeline.processed_calls) == 0
    # But RawPage for job2 was created
    assert RawPage.objects.filter(job=job2).count() == 1


@pytest.mark.django_db
def test_crawler_handles_http_errors_and_fetch_exceptions() -> None:
    """Verifies crawler handles HTTP errors and network exceptions by skipping."""
    source = CrawlSource.objects.create(
        name="NAMUNA Sayt",
        start_url="https://example.uz",
        kind=CrawlSource.Kind.DOCUMENT,
        publisher="namuna.uz",
        max_pages=5,
    )

    responses: dict[str, FetchResult | Exception] = {
        "https://example.uz": FetchResult(
            url="https://example.uz",
            final_url="https://example.uz",
            status=200,
            content_type="text/html",
            body=(
                b"<html><body>"
                b'<a href="/broken">Broken</a>'
                b'<a href="/error500">Error 500</a>'
                b'<a href="/ok">OK</a>'
                b"</body></html>"
            ),
        ),
        "https://example.uz/broken": RuntimeError("Network connection lost"),
        "https://example.uz/error500": FetchResult(
            url="https://example.uz/error500",
            final_url="https://example.uz/error500",
            status=500,
            content_type="text/html",
            body=b"Server error",
        ),
        "https://example.uz/ok": FetchResult(
            url="https://example.uz/ok",
            final_url="https://example.uz/ok",
            status=200,
            content_type="text/html",
            body=b"<html><body>OK Page</body></html>",
        ),
    }

    fetcher = FakeFetcher(responses)
    pipeline = RecordingPipeline()
    limiter = _make_limiter()
    robots = FakeRobotsPolicy()

    job = crawl(source, fetcher=fetcher, robots=robots, limiter=limiter, pipeline=pipeline)

    assert job.status == CrawlJob.Status.DONE
    assert job.pages_fetched == 2
    assert job.pages_skipped == 2


@pytest.mark.django_db
def test_crawler_saves_pdf_extension() -> None:
    """Verifies crawler saves PDF content with .pdf extension."""
    source = CrawlSource.objects.create(
        name="NAMUNA PDF Sayt",
        start_url="https://example.uz/file.pdf",
        kind=CrawlSource.Kind.DOCUMENT,
        publisher="namuna.uz",
        max_pages=1,
    )

    responses: dict[str, FetchResult | Exception] = {
        "https://example.uz/file.pdf": FetchResult(
            url="https://example.uz/file.pdf",
            final_url="https://example.uz/file.pdf",
            status=200,
            content_type="application/pdf",
            body=b"%PDF-1.4 sample pdf content",
        ),
    }

    fetcher = FakeFetcher(responses)
    pipeline = RecordingPipeline()
    limiter = _make_limiter()
    robots = FakeRobotsPolicy()

    job = crawl(source, fetcher=fetcher, robots=robots, limiter=limiter, pipeline=pipeline)

    assert job.status == CrawlJob.Status.DONE
    raw_page = RawPage.objects.get(job=job)
    assert Path(raw_page.raw_path).suffix == ".pdf"


@pytest.mark.django_db
def test_crawler_invalid_regex_marks_job_failed() -> None:
    """Verifies invalid regex pattern raises exception and marks job as FAILED."""
    source = CrawlSource.objects.create(
        name="NAMUNA Xato Regex",
        start_url="https://example.uz",
        allowed_url_pattern="[unclosed bracket",
        kind=CrawlSource.Kind.DOCUMENT,
        publisher="namuna.uz",
    )

    fetcher = FakeFetcher({})
    pipeline = RecordingPipeline()
    limiter = _make_limiter()
    robots = FakeRobotsPolicy()

    with pytest.raises(re.error):
        crawl(source, fetcher=fetcher, robots=robots, limiter=limiter, pipeline=pipeline)

    job = CrawlJob.objects.get(source=source)
    assert job.status == CrawlJob.Status.FAILED
    assert "unterminated character set" in job.error or "bracket" in job.error
