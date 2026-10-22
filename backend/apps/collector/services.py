"""Crawl scheduling (web side). Crawling itself lives in ``runner`` (worker image only)."""

from django.db import transaction

from apps.collector.models import CrawlJob, CrawlSource


def start_crawl(source: CrawlSource) -> CrawlJob:
    """Queue a crawl job and enqueue it for the worker once the transaction commits.

    Args:
        source: The source to crawl.

    Returns:
        The queued job.
    """
    from apps.collector.tasks import crawl_source  # noqa: PLC0415 (tasks imports runner lazily)

    job = CrawlJob.objects.create(source=source)
    transaction.on_commit(lambda: crawl_source.enqueue(str(job.id)))
    return job
