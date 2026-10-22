"""Tests for the admin dashboard KPIs and page."""

import pytest
from django.test import Client
from django.utils import timezone

from apps.accounts.models import User
from apps.chat.models import Conversation, Feedback, Message
from apps.common.dashboard import dashboard_kpis
from apps.corpus.models import Chunk, Document

pytestmark = pytest.mark.django_db


def test_kpis_count_everything(user: User) -> None:
    """Documents, embedded chunks, questions and feedback are counted."""
    document = Document.objects.create(
        title="NAMUNA",
        url="https://example.org/1",
        publisher="x",
        fetched_at=timezone.now(),
        text="NAMUNA",
        text_hash="x",
        corpus_version="t",
        status="approved",
    )
    Chunk.objects.create(document=document, order=0, text="a", text_normalized="a", char_count=1)
    conversation = Conversation.objects.create(user=user)
    Message.objects.create(conversation=conversation, role="user", text="NAMUNA?")
    answer = Message.objects.create(conversation=conversation, role="assistant")
    Feedback.objects.create(message=answer, rating=1)
    tiles = {kpi.title: kpi for kpi in dashboard_kpis()}
    assert tiles["Documents"].value == "1 approved"
    assert (tiles["Chunks embedded"].value, tiles["Chunks embedded"].progress) == ("0%", 0)
    assert tiles["Questions today"].value == "1"
    assert tiles["Thumbs up"].value == "100%"
    assert tiles["Tokens today"].value == "0"


def test_dashboard_page_renders(db: None) -> None:
    """The admin index shows the tiles."""
    client = Client()
    client.force_login(User.objects.create_superuser("root@example.com", "pw-1234567890"))
    page = client.get("/admin/").content.decode()
    assert "Chunks embedded" in page
    assert "Tokens today" in page
