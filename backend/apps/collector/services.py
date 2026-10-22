from django.db import transaction

from apps.collector.crawler import Crawler
from apps.collector.extraction import GeminiOfficeExtractor, GeminiOfficeTypeClassifier
from apps.collector.fetchers import BrowserFetcher, Fetcher, HttpFetcher
from apps.collector.models import CrawlJob, CrawlSource
from apps.collector.pipelines import DocumentPipeline, OfficePipeline, Pipeline


def start_crawl(source: CrawlSource) -> CrawlJob:
    """Queue a crawl job and enqueue it for the worker once the transaction commits.

    Args:
        source: The source to crawl.

    Returns:
        The queued job.
    """
    from apps.collector.tasks import crawl_source  # noqa: PLC0415 (tasks imports services)

    job = CrawlJob.objects.create(source=source)
    transaction.on_commit(lambda: crawl_source.enqueue(str(job.id)))
    return job


def build_crawler(source: CrawlSource) -> Crawler:
    """Wire the production crawler for a source (browser or HTTP; document or office).

    Args:
        source: The source to crawl.
    """
    fetcher: Fetcher = BrowserFetcher() if source.use_browser else HttpFetcher()
    pipeline: Pipeline = (
        OfficePipeline(GeminiOfficeExtractor())
        if source.kind == CrawlSource.Kind.OFFICE
        else DocumentPipeline(GeminiOfficeTypeClassifier())
    )
    return Crawler(fetcher=fetcher, pipeline=pipeline)


def run_job(job: CrawlJob) -> CrawlJob:
    """Run one crawl job with the production wiring.

    Args:
        job: A queued job.
    """
    return build_crawler(job.source).run(job)
