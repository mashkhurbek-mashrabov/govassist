"""Background jobs for the collector (run by ``db_worker`` in the crawler image)."""

from django.tasks import task

from apps.collector.models import CrawlJob


@task
def crawl_source(job_id: str) -> int:
    """Run a queued crawl job.

    Args:
        job_id: The CrawlJob UUID as a string (task args must be JSON).

    Returns:
        Pages fetched.
    """
    from apps.collector import runner  # noqa: PLC0415 (crawler-only deps, worker image)

    job = CrawlJob.objects.select_related("source").get(id=job_id)
    return runner.run_job(job).pages_fetched
