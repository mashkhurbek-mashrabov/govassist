"""Tests for start_crawl, the crawl task/command and the admin (changelists + actions)."""

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.admin.sites import site
from django.core.management import CommandError, call_command
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.collector import runner, services
from apps.collector.crawler import Crawler
from apps.collector.fetchers import BrowserFetcher, HttpFetcher
from apps.collector.models import CrawlJob, CrawlSource
from apps.collector.pipelines import DocumentPipeline, OfficePipeline
from apps.common.constants import ReviewStatus
from apps.corpus.models import Document
from apps.geo.models import District
from apps.offices.models import Office, OfficeType

pytestmark = pytest.mark.django_db


def _source(**extra: object) -> CrawlSource:
    """A NAMUNA source."""
    defaults: dict[str, object] = {
        "name": "NAMUNA",
        "start_url": "https://example.org/",
        "publisher": "x",
    }
    return CrawlSource.objects.create(**(defaults | extra))


def test_start_crawl_enqueues_on_commit(
    django_capture_on_commit_callbacks: Callable[..., Any],
) -> None:
    """A queued job is created and the task runs after commit (inline in tests)."""
    source = _source()
    with (
        patch("apps.collector.runner.run_job") as run_job,
        django_capture_on_commit_callbacks(execute=True),
    ):
        run_job.return_value = MagicMock(pages_fetched=3)
        job = services.start_crawl(source)
    assert job.status == CrawlJob.Status.QUEUED
    assert run_job.call_args.args[0].id == job.id


def test_build_crawler_picks_fetcher_and_pipeline(office_type: OfficeType) -> None:
    """Browser/HTTP and document/office wiring follow the source settings."""
    with (
        patch("apps.collector.runner.GeminiOfficeTypeClassifier"),
        patch("apps.collector.runner.GeminiOfficeExtractor"),
    ):
        document_crawler = runner.build_crawler(_source())
        office_crawler = runner.build_crawler(
            _source(kind="office", office_type=office_type, use_browser=True)
        )
    assert isinstance(document_crawler._fetcher, HttpFetcher)
    assert isinstance(document_crawler._pipeline, DocumentPipeline)
    assert isinstance(office_crawler._fetcher, BrowserFetcher)
    assert isinstance(office_crawler._pipeline, OfficePipeline)


def test_crawl_command(capsys: pytest.CaptureFixture[str]) -> None:
    """--source by name or id and --all run jobs; an unknown source is an error."""
    source = _source()

    def finish(job: CrawlJob) -> CrawlJob:
        """Pretend the crawl succeeded."""
        job.status, job.pages_fetched = CrawlJob.Status.DONE, 1
        return job

    with (
        patch.object(Crawler, "run", side_effect=finish),
        patch("apps.collector.runner.GeminiOfficeTypeClassifier"),
    ):
        call_command("crawl", "--source", "NAMUNA")
        call_command("crawl", "--source", str(source.id))
        call_command("crawl", "--all")
    assert capsys.readouterr().out.count("NAMUNA: done, fetched 1") == 3
    with pytest.raises(CommandError):
        call_command("crawl", "--source", "missing")


@pytest.fixture
def admin_client(db: None) -> Client:
    """A client logged in as a superuser."""
    client = Client()
    client.force_login(User.objects.create_superuser("root@example.com", "pw-1234567890"))
    return client


def test_every_admin_changelist_and_add_view(admin_client: Client) -> None:
    """Every registered model's changelist and add page renders."""
    for model in site._registry:
        meta = model._meta
        changelist = reverse(f"admin:{meta.app_label}_{meta.model_name}_changelist")
        assert admin_client.get(changelist).status_code == 200, changelist
        add = reverse(f"admin:{meta.app_label}_{meta.model_name}_add")
        assert admin_client.get(add).status_code in {200, 403}, add
    assert admin_client.get(reverse("admin:index")).status_code == 200


def _act(client: Client, model: str, action: str, ids: list[object]) -> None:
    """Run an admin action on ``ids``."""
    url = reverse(f"admin:{model}_changelist")
    response = client.post(url, {"action": action, "_selected_action": [str(i) for i in ids]})
    assert response.status_code == 302


def test_admin_actions(admin_client: Client, office_type: OfficeType, district: District) -> None:
    """Run crawl, approve/reject/re-index documents, approve/reject offices."""
    source = _source()
    with patch("apps.collector.admin.start_crawl") as start:
        _act(admin_client, "collector_crawlsource", "run_crawl", [source.id])
    start.assert_called_once()

    document = Document.objects.create(
        title="NAMUNA",
        url="https://example.org/d",
        publisher="x",
        fetched_at=timezone.now(),
        text="NAMUNA",
        text_hash="x",
        corpus_version="t",
    )
    with patch("apps.corpus.tasks.index_document") as index:
        _act(admin_client, "corpus_document", "approve", [document.id])
        _act(admin_client, "corpus_document", "reindex", [document.id])
    assert Document.objects.get(id=document.id).status == ReviewStatus.APPROVED
    assert (
        admin_client.get(reverse("admin:corpus_document_change", args=[document.id])).status_code
        == 200
    )
    _act(admin_client, "corpus_document", "reject", [document.id])
    assert Document.objects.get(id=document.id).status == ReviewStatus.REJECTED
    del index

    office = Office.objects.create(
        office_type=office_type,
        name="NAMUNA",
        address="NAMUNA 1",
        district=district,
        region=district.region,
        source_url="https://example.org/o",
        data_as_of=timezone.localdate(),
    )
    page = admin_client.get(reverse("admin:offices_office_change", args=[office.id])).content
    assert b"google.com/maps/search" in page
    _act(admin_client, "offices_office", "approve", [office.id])
    assert Office.objects.get(id=office.id).status == ReviewStatus.APPROVED
    _act(admin_client, "offices_office", "reject", [office.id])
    assert Office.objects.get(id=office.id).status == ReviewStatus.REJECTED


def test_crawl_command_continues_after_a_failure(capsys: pytest.CaptureFixture[str]) -> None:
    """One failing source is reported; the others still run; the command exits with an error."""
    _source(name="NAMUNA a")
    _source(name="NAMUNA b")
    calls: list[str] = []

    def run(job: CrawlJob, **kwargs: object) -> CrawlJob:
        """Fail for source a."""
        calls.append(job.source.name)
        if job.source.name == "NAMUNA a":
            msg = "boom"
            raise ConnectionError(msg)
        return job

    with (
        patch("apps.collector.runner.run_job", side_effect=run),
        pytest.raises(CommandError, match="NAMUNA a"),
    ):
        call_command("crawl", "--all")
    assert sorted(calls) == ["NAMUNA a", "NAMUNA b"]
    assert "NAMUNA a: failed: ConnectionError: boom" in capsys.readouterr().err
