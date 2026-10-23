"""Admin changelists make a fixed number of queries: no N+1 on foreign-key columns.

Django already joins FK columns of ``list_display``; the explicit ``list_select_related``
narrows that join to the shown columns. This test guards against new per-row queries
(for example a callable column that follows a relation).
"""

from collections.abc import Callable
from typing import Any

import pytest
from django.db import connection
from django.db.models import Model
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.accounts.models import User
from apps.chat.models import Conversation, Feedback, Message
from apps.collector.models import CrawlJob, CrawlSource
from apps.corpus.models import Chunk
from apps.geo.models import District, Region
from apps.offices.models import Office, OfficeType, ServiceOffice
from conftest import make_office, make_user, namuna_document

pytestmark = pytest.mark.django_db
ROWS = 5


def _conversation(i: int) -> Conversation:
    """A NAMUNA conversation with one answered message and its feedback."""
    owner = make_user(f"namuna{i}@example.com")
    conversation = Conversation.objects.create(user=owner, title=f"NAMUNA {i}", language="uz-Latn")
    message = Message.objects.create(
        conversation=conversation, role=Message.Role.ASSISTANT, language="uz-Latn"
    )
    Feedback.objects.create(message=message, rating=1)
    return conversation


def _crawl_job(i: int) -> CrawlJob:
    """A NAMUNA crawl job on its own source."""
    source = CrawlSource.objects.create(
        name=f"NAMUNA {i}", start_url=f"https://namuna{i}.example/", publisher="namuna"
    )
    return CrawlJob.objects.create(source=source)


def _office(i: int) -> Office:
    """A NAMUNA office (and a service-office link) in its own region and district."""
    region = Region.objects.create(id=9800 + i, name_uz_latn=f"NAMUNA {i} viloyati")
    district = District.objects.create(id=9800100 + i, region=region, name_uz_latn=f"NAMUNA {i}")
    office_type = OfficeType.objects.create(code=f"namuna{i}", name_uz_latn=f"NAMUNA {i}")
    document = namuna_document(f"NAMUNA matn {i}", slug=f"namuna{i}")
    ServiceOffice.objects.create(document=document, office_type=office_type)
    return make_office(office_type, district)


MAKERS: dict[type[Model], Callable[[int], Model]] = {
    Conversation: _conversation,
    Message: _conversation,
    Feedback: _conversation,
    Chunk: lambda i: namuna_document(f"NAMUNA matn {i}", slug=f"chunk{i}"),
    District: _office,
    CrawlJob: _crawl_job,
    User: lambda i: make_user(f"u{i}@example.com"),
    Office: _office,
    ServiceOffice: _office,
}


@pytest.mark.parametrize("model", list(MAKERS), ids=lambda model: model.__name__)
def test_changelist_queries_do_not_grow_with_rows(
    admin_client: Client,
    django_assert_max_num_queries: Callable[[int], Any],
    model: type[Model],
) -> None:
    """Five rows cost no more queries than one (list_select_related on FK columns)."""
    meta = model._meta
    url = reverse(f"admin:{meta.app_label}_{meta.model_name}_changelist")
    MAKERS[model](0)
    with CaptureQueriesContext(connection) as one_row:
        assert admin_client.get(url).status_code == 200
    for i in range(1, ROWS):
        MAKERS[model](i)
    with django_assert_max_num_queries(len(one_row)):
        assert admin_client.get(url).status_code == 200
