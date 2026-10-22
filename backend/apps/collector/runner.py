"""Crawler wiring for the worker image (needs the crawler-only parsing dependencies)."""

from apps.collector.crawler import Crawler
from apps.collector.extraction import GeminiOfficeExtractor, GeminiOfficeTypeClassifier
from apps.collector.fetchers import BrowserFetcher, Fetcher, HttpFetcher
from apps.collector.models import CrawlJob, CrawlSource
from apps.collector.pipelines import DocumentPipeline, OfficePipeline, Pipeline


def build_crawler(source: CrawlSource, *, force: bool = False) -> Crawler:
    """Wire the production crawler for a source (browser or HTTP; document or office).

    Args:
        source: The source to crawl.
        force: Re-process unchanged pages.
    """
    fetcher: Fetcher = BrowserFetcher() if source.use_browser else HttpFetcher()
    pipeline: Pipeline = (
        OfficePipeline(GeminiOfficeExtractor())
        if source.kind == CrawlSource.Kind.OFFICE
        else DocumentPipeline(GeminiOfficeTypeClassifier())
    )
    return Crawler(fetcher=fetcher, pipeline=pipeline, force=force)


def run_job(job: CrawlJob, *, force: bool = False) -> CrawlJob:
    """Run one crawl job with the production wiring.

    Args:
        job: A queued job.
        force: Re-process unchanged pages.
    """
    return build_crawler(job.source, force=force).run(job)
