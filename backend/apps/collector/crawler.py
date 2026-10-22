"""Breadth-first search crawler engine for documents and office directories."""

import hashlib
import logging
import re
import urllib.parse
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Protocol

from django.conf import settings
from django.utils import timezone

from apps.collector.fetchers import Fetcher, FetchResult
from apps.collector.models import CrawlJob, CrawlSource, RawPage
from apps.collector.parsers import parse
from apps.collector.pipelines import Pipeline

logger = logging.getLogger(__name__)

HTTP_OK = 200
HTTP_BAD_REQUEST = 400


class RobotsChecker(Protocol):
    """Protocol for checking whether a URL is allowed by domain robots policy."""

    def can_fetch(self, url: str) -> bool:
        """Check whether fetching the given URL is allowed.

        Args:
            url: Candidate URL to test.

        Returns:
            True if allowed, False if disallowed.
        """
        ...


class RateLimiter(Protocol):
    """Protocol for polite host rate limiting."""

    def wait(self, url: str) -> None:
        """Wait before fetching the URL if rate limit requires.

        Args:
            url: Target URL to be fetched.
        """
        ...


def _save_raw_page(
    source: CrawlSource,
    job: CrawlJob,
    page: FetchResult,
    url: str,
    fetched_at: datetime,
) -> tuple[RawPage, bool]:
    """Store raw fetched bytes to disk and create a RawPage DB record.

    Args:
        source: CrawlSource being crawled.
        job: Active CrawlJob.
        page: Fetched page result.
        url: Page URL.
        fetched_at: Fetch timestamp.

    Returns:
        Tuple of (RawPage, is_unchanged_flag).
    """
    content_hash = hashlib.sha256(page.body).hexdigest()
    is_pdf = (
        page.content_type == "application/pdf"
        or url.lower().endswith(".pdf")
        or page.final_url.lower().endswith(".pdf")
    )
    ext = "pdf" if is_pdf else "html"

    raw_dir = Path(settings.RAW_DATA_DIR) / str(source.id)
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file_path = raw_dir / f"{content_hash}.{ext}"
    if not raw_file_path.exists():
        raw_file_path.write_bytes(page.body)

    prev_page = RawPage.objects.filter(url=url).exclude(job=job).order_by("-fetched_at").first()
    is_unchanged = prev_page is not None and prev_page.content_hash == content_hash

    raw_page = RawPage.objects.create(
        job=job,
        url=url,
        http_status=page.status,
        content_type=page.content_type,
        content_hash=content_hash,
        raw_path=str(raw_file_path),
        fetched_at=fetched_at,
    )
    return raw_page, is_unchanged


def _enqueue_links(
    page: FetchResult,
    source: CrawlSource,
    *,
    start_host: str,
    url_pattern: re.Pattern[str] | None,
    visited: set[str],
    queue: deque[str],
) -> None:
    """Parse out page links and enqueue unvisited, in-scope URLs.

    Args:
        page: Fetched page result.
        source: CrawlSource configuration.
        start_host: Hostname restriction for BFS.
        url_pattern: Optional regex pattern restricting allowed URLs.
        visited: Set of already seen or visited URLs.
        queue: Active BFS queue.
    """
    try:
        parsed_page = parse(page, source)
        for link in parsed_page.links:
            if link in visited:
                continue
            link_netloc = urllib.parse.urlsplit(link).netloc.lower()
            if link_netloc != start_host:
                continue
            if url_pattern is not None and not url_pattern.search(link):
                continue
            queue.append(link)
    except Exception as exc:
        logger.warning("Failed to parse links from %s: %s", page.url, exc)


def _fetch_page(
    url: str,
    *,
    start_host: str,
    robots: RobotsChecker,
    limiter: RateLimiter,
    fetcher: Fetcher,
    job: CrawlJob,
) -> FetchResult | None:
    """Validate, rate-limit, and fetch a page, recording skips on failure.

    Args:
        url: Candidate page URL.
        start_host: Allowed base hostname.
        robots: Domain robots policy checker.
        limiter: Polite host rate limiter.
        fetcher: HTTP or browser fetcher client.
        job: Active crawl job for tracking metrics.

    Returns:
        FetchResult if successful, or None if skipped/failed.
    """
    parsed_url = urllib.parse.urlsplit(url)
    if parsed_url.netloc.lower() != start_host:
        logger.debug("Skipping off-host URL: %s", url)
        return None

    if not robots.can_fetch(url):
        logger.info("URL disallowed by robots.txt: %s", url)
        job.pages_skipped += 1
        job.save(update_fields=["pages_skipped"])
        return None

    limiter.wait(url)

    try:
        page = fetcher.fetch(url)
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        job.pages_skipped += 1
        job.save(update_fields=["pages_skipped"])
        return None

    if page.status < HTTP_OK or page.status >= HTTP_BAD_REQUEST:
        logger.warning("HTTP error %d when fetching %s", page.status, url)
        job.pages_skipped += 1
        job.save(update_fields=["pages_skipped"])
        return None

    return page


def crawl(
    source: CrawlSource,
    *,
    fetcher: Fetcher,
    robots: RobotsChecker,
    limiter: RateLimiter,
    pipeline: Pipeline,
    job: CrawlJob | None = None,
) -> CrawlJob:
    """Execute a breadth-first search crawl for a configured source.

    Follows links on the same host matching ``source.allowed_url_pattern``
    up to ``source.max_pages``. Disallowed robots.txt URLs or HTTP errors
    are recorded as skipped pages. Raw fetched bytes are stored in
    ``settings.RAW_DATA_DIR``. Unchanged content hashes skip pipeline
    execution while still allowing link discovery.

    Args:
        source: Source configuration governing the crawl.
        fetcher: HTTP or browser fetcher client.
        robots: Robots.txt checker for the domain.
        limiter: Host-level polite rate limiter.
        pipeline: Target ingestion pipeline (DocumentPipeline or OfficePipeline).
        job: Optional pre-created CrawlJob instance.

    Returns:
        Completed or failed CrawlJob instance.

    Raises:
        re.error: If ``allowed_url_pattern`` is an invalid regular expression.
        Exception: If an unhandled error occurs during the crawl run.
    """
    if job is None:
        job = CrawlJob.objects.create(
            source=source,
            status=CrawlJob.Status.RUNNING,
            started_at=timezone.now(),
        )
    else:
        job.status = CrawlJob.Status.RUNNING
        job.started_at = timezone.now()
        job.save(update_fields=["status", "started_at"])

    try:
        url_pattern: re.Pattern[str] | None = None
        if source.allowed_url_pattern:
            url_pattern = re.compile(source.allowed_url_pattern)

        start_parsed = urllib.parse.urlsplit(source.start_url)
        start_host = start_parsed.netloc.lower()

        queue: deque[str] = deque([source.start_url])
        visited: set[str] = set()

        while queue and job.pages_fetched < source.max_pages:
            url = queue.popleft()
            if url in visited:
                continue
            visited.add(url)

            page = _fetch_page(
                url,
                start_host=start_host,
                robots=robots,
                limiter=limiter,
                fetcher=fetcher,
                job=job,
            )
            if page is None:
                continue

            visited.add(page.final_url)
            job.pages_fetched += 1
            job.save(update_fields=["pages_fetched"])
            fetched_at = timezone.now()

            _, is_unchanged = _save_raw_page(source, job, page, url, fetched_at)

            if is_unchanged:
                logger.info("Content hash unchanged for %s; skipping pipeline.", url)
            else:
                pipeline.process(
                    source,
                    page,
                    url=page.final_url or url,
                    fetched_at=fetched_at,
                )

            if job.pages_fetched < source.max_pages:
                _enqueue_links(
                    page,
                    source,
                    start_host=start_host,
                    url_pattern=url_pattern,
                    visited=visited,
                    queue=queue,
                )

        job.status = CrawlJob.Status.DONE
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "finished_at", "pages_fetched", "pages_skipped"])

        source.last_crawled_at = job.finished_at
        source.save(update_fields=["last_crawled_at"])

    except Exception as exc:
        logger.exception("Crawl execution failed for source %s: %s", source.name, exc)
        job.status = CrawlJob.Status.FAILED
        job.error = str(exc)
        job.finished_at = timezone.now()
        job.save(
            update_fields=[
                "status",
                "error",
                "finished_at",
                "pages_fetched",
                "pages_skipped",
            ]
        )
        raise

    return job
