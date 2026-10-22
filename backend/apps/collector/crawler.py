"""Breadth-first crawl of one source: robots, rate limit, raw storage, parse once, pipeline."""

import hashlib
import logging
import re
from collections import deque
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from apps.collector.fetchers import Fetcher, FetchResult, HostRateLimiter, RobotsPolicy, host_of
from apps.collector.models import CrawlJob, CrawlSource, RawPage
from apps.collector.parsers import ParsedPage, parse
from apps.collector.pipelines import Pipeline

logger = logging.getLogger(__name__)

HTTP_OK_MIN, HTTP_OK_MAX = 200, 299


def _digest(page: FetchResult) -> str:
    """sha256 of the page bytes."""
    return hashlib.sha256(page.body).hexdigest()


def _is_unchanged(page: FetchResult) -> bool:
    """True when this URL was already stored with the same content."""
    return RawPage.objects.filter(url=page.url, content_hash=_digest(page)).exists()


def _store_raw(source: CrawlSource, job: CrawlJob, page: FetchResult) -> None:
    """Save the bytes under ``RAW_DATA_DIR/<source>/<sha256>.<ext>`` and record a RawPage.

    Called after the pipeline succeeded, so a failed page is processed again next time.

    Args:
        source: The source being crawled.
        job: The running job.
        page: The fetched page.
    """
    digest = _digest(page)
    folder = Path(settings.RAW_DATA_DIR) / str(source.id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{digest}.{'pdf' if page.is_pdf else 'html'}"
    if not path.exists():
        path.write_bytes(page.body)
    RawPage.objects.create(
        job=job,
        url=page.url,
        http_status=page.status,
        content_type=page.content_type,
        content_hash=digest,
        raw_path=str(path),
        fetched_at=timezone.now(),
    )


class Crawler:
    """Runs one crawl job; every collaborator is injected so tests use fakes.

    ``force`` re-runs the pipeline on unchanged pages (after a parser change).
    """

    def __init__(
        self,
        *,
        fetcher: Fetcher,
        pipeline: Pipeline,
        robots: RobotsPolicy | None = None,
        limiter: HostRateLimiter | None = None,
        force: bool = False,
    ) -> None:
        self._fetcher = fetcher
        self._pipeline = pipeline
        self._robots = robots or RobotsPolicy()
        self._limiter = limiter or HostRateLimiter()
        self._force = force

    def _skip(self, job: CrawlJob, url: str, reason: str) -> None:
        """Count and log a page that was not processed."""
        job.pages_skipped += 1
        logger.info("Page skipped", extra={"url": url, "reason": reason})

    def _fetch(self, job: CrawlJob, url: str) -> FetchResult | None:
        """Fetch one URL politely; None (counted as skipped) when not allowed or not 2xx."""
        if not self._robots.allowed(url):
            self._skip(job, url, "robots.txt")
            return None
        self._limiter.wait(url)
        page = self._fetcher.fetch(url)
        if not HTTP_OK_MIN <= page.status <= HTTP_OK_MAX:
            self._skip(job, url, f"HTTP {page.status}")
            return None
        return page

    def _follow(self, source: CrawlSource, parsed: ParsedPage) -> list[str]:
        """Links to follow: same host as the start URL and matching the source pattern."""
        if not source.allowed_url_pattern:
            return []
        pattern = re.compile(source.allowed_url_pattern)
        start_host = host_of(source.start_url)
        return [
            link for link in parsed.links if host_of(link) == start_host and pattern.search(link)
        ]

    def _visit(
        self, source: CrawlSource, job: CrawlJob, url: str, fetched_at: datetime
    ) -> list[str]:
        """Fetch, store, parse and process one page; return the links to follow."""
        page = self._fetch(job, url)
        if page is None:
            return []
        job.pages_fetched += 1
        parsed = parse(page)
        if not self._force and _is_unchanged(page):
            self._skip(job, url, "unchanged")
        else:
            self._pipeline.process(source, parsed, url=page.final_url, fetched_at=fetched_at)
        _store_raw(source, job, page)
        return self._follow(source, parsed)

    def run(self, job: CrawlJob) -> CrawlJob:
        """Crawl ``job.source`` breadth-first, up to ``max_pages`` fetched pages.

        A failure marks the job failed with its error and is re-raised (never swallowed).

        Args:
            job: A queued job.

        Returns:
            The finished job.
        """
        source = job.source
        job.status, job.started_at = CrawlJob.Status.RUNNING, timezone.now()
        job.save(update_fields=["status", "started_at"])
        queue, seen = deque([source.start_url]), {source.start_url}
        try:
            while queue and job.pages_fetched < source.max_pages:
                for link in self._visit(source, job, queue.popleft(), timezone.now()):
                    if link not in seen:
                        seen.add(link)
                        queue.append(link)
        except Exception as exc:
            job.status, job.error = CrawlJob.Status.FAILED, f"{type(exc).__name__}: {exc}"
            raise
        else:
            job.status = CrawlJob.Status.DONE
            source.last_crawled_at = timezone.now()
            source.save(update_fields=["last_crawled_at"])
        finally:
            job.finished_at = timezone.now()
            job.save()
        return job
