"""Tests for the BFS crawler with fake fetcher, robots and pipeline (no network)."""

from datetime import datetime
from pathlib import Path

import pytest
from django.conf import settings

from apps.collector.crawler import Crawler
from apps.collector.fetchers import FetchResult, HostRateLimiter
from apps.collector.models import CrawlJob, CrawlSource, RawPage
from apps.collector.parsers import ParsedPage

pytestmark = pytest.mark.django_db
START = "https://example.org/start"


class FakeFetcher:
    """Serves preset pages; unknown URLs are 404."""

    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.fetched: list[str] = []

    def fetch(self, url: str) -> FetchResult:
        """Return the preset page."""
        self.fetched.append(url)
        body = self.pages.get(url)
        status = 200 if body is not None else 404
        return FetchResult(url, url, status, "text/html", (body or "").encode())


class FakeRobots:
    """Disallows URLs containing 'private'."""

    def allowed(self, url: str) -> bool:
        """Allow everything except private paths."""
        return "private" not in url


class RecordingPipeline:
    """Remembers what it processed; can fail on demand."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.urls: list[str] = []

    def process(
        self, source: CrawlSource, page: ParsedPage, *, url: str, fetched_at: datetime
    ) -> None:
        """Record or fail."""
        if self.fail:
            msg = "pipeline broke"
            raise RuntimeError(msg)
        self.urls.append(url)


def _page(*links: str) -> str:
    """NAMUNA HTML linking to ``links``."""
    anchors = "".join(f'<a href="{link}">x</a>' for link in links)
    return f"<title>NAMUNA</title><p>NAMUNA matn</p>{anchors}"


def _source(**extra: object) -> CrawlSource:
    """A NAMUNA document source."""
    defaults: dict[str, object] = {"name": "NAMUNA", "start_url": START, "publisher": "example.org"}
    return CrawlSource.objects.create(**(defaults | extra))


def _crawl(source: CrawlSource, fetcher: FakeFetcher, pipeline: RecordingPipeline) -> CrawlJob:
    """Run one job with fakes and no sleeping."""
    crawler = Crawler(
        fetcher=fetcher,
        pipeline=pipeline,
        robots=FakeRobots(),  # type: ignore[arg-type]
        limiter=HostRateLimiter(1000, sleep=lambda s: None),
    )
    return crawler.run(CrawlJob.objects.create(source=source))


SITE = {
    START: _page("/docs/1", "/docs/private", "/other", "https://elsewhere.org/docs/2", "/docs/404"),
    "https://example.org/docs/1": _page(START, "/docs/3"),
    "https://example.org/docs/3": _page(),
    "https://example.org/other": _page(),
}


def test_bfs_follows_matching_same_host_links() -> None:
    """Pattern + same host are followed; robots and 404s are skipped; raw bytes stored."""
    source = _source(allowed_url_pattern=r"/docs/", max_pages=10)
    pipeline = RecordingPipeline()
    job = _crawl(source, FakeFetcher(SITE), pipeline)
    assert job.status == CrawlJob.Status.DONE
    assert pipeline.urls == [START, "https://example.org/docs/1", "https://example.org/docs/3"]
    assert (job.pages_fetched, job.pages_skipped) == (3, 2)
    source.refresh_from_db()
    assert source.last_crawled_at is not None
    raw = RawPage.objects.filter(job=job).first()
    assert raw is not None
    assert Path(raw.raw_path).read_bytes()
    assert Path(raw.raw_path).is_relative_to(Path(settings.RAW_DATA_DIR))


def test_max_pages_and_no_pattern() -> None:
    """Without a pattern only the start URL is crawled; max_pages caps fetching."""
    job = _crawl(_source(), FakeFetcher(SITE), RecordingPipeline())
    assert job.pages_fetched == 1
    capped = _crawl(
        _source(allowed_url_pattern=".", max_pages=2), FakeFetcher(SITE), RecordingPipeline()
    )
    assert capped.pages_fetched == 2


def test_unchanged_pages_skip_the_pipeline() -> None:
    """A second crawl of identical content does not re-run the pipeline."""
    source = _source()
    _crawl(source, FakeFetcher(SITE), RecordingPipeline())
    second = RecordingPipeline()
    job = _crawl(source, FakeFetcher(SITE), second)
    assert second.urls == []
    assert job.pages_skipped == 1


def test_failure_marks_job_failed_and_reraises() -> None:
    """A pipeline error fails the job with its message, and the page is not marked seen."""
    source = _source()
    with pytest.raises(RuntimeError, match="pipeline broke"):
        _crawl(source, FakeFetcher(SITE), RecordingPipeline(fail=True))
    job = CrawlJob.objects.get(source=source)
    assert job.status == CrawlJob.Status.FAILED
    assert job.error == "RuntimeError: pipeline broke"
    assert job.finished_at is not None
    assert not RawPage.objects.exists()
