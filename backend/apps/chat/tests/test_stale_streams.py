"""Atomic turn creation and expiry of answers stuck in ``streaming``."""

from datetime import timedelta

import pytest
from django.conf import settings
from django.core.management import call_command
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.chat import services
from apps.chat.models import Conversation, Message
from apps.common.constants import Lang

pytestmark = pytest.mark.django_db


def _streaming(user: User, *, age_s: int) -> Message:
    """A conversation whose answer started streaming ``age_s`` seconds ago."""
    conversation, _, assistant = services.open_turn(user, None, "NAMUNA savol", Lang.UZ_LATN)
    Message.objects.filter(pk=assistant.pk).update(
        created_at=timezone.now() - timedelta(seconds=age_s)
    )
    assistant.refresh_from_db()
    assert assistant.conversation_id == conversation.id
    return assistant


def test_open_turn_creates_all_rows_or_none(user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    """A failure while creating the answer leaves no orphan conversation or question."""
    real_create = Message.objects.create

    def fail_on_answer(**fields: object) -> Message:
        """Create the user message; fail on the assistant row."""
        if fields.get("role") == Message.Role.ASSISTANT:
            raise IntegrityError("NAMUNA")
        return real_create(**fields)

    monkeypatch.setattr(Message.objects, "create", fail_on_answer)
    with pytest.raises(IntegrityError):
        services.open_turn(user, None, "NAMUNA savol", Lang.UZ_LATN)
    assert (Conversation.objects.count(), Message.objects.count()) == (0, 0)


def test_only_answers_older_than_the_lock_ttl_expire(user: User) -> None:
    """Dead streams become failed/stopped; a live (recent) one is left alone."""
    ttl = settings.STREAM_LOCK_TTL_S
    dead = _streaming(user, age_s=ttl + 5)
    live = _streaming(user, age_s=5)
    assert services.expire_stale_streams() == 1
    dead.refresh_from_db()
    live.refresh_from_db()
    assert (dead.status, dead.error_code) == (Message.Status.FAILED, "stopped")
    assert live.status == Message.Status.STREAMING


def test_conversation_detail_expires_its_dead_stream(auth_api: APIClient, user: User) -> None:
    """Reading a conversation never shows a dead answer as still writing."""
    dead = _streaming(user, age_s=settings.STREAM_LOCK_TTL_S + 5)
    other = _streaming(user, age_s=settings.STREAM_LOCK_TTL_S + 5)
    body = auth_api.get(f"/api/v1/conversations/{dead.conversation_id}").json()
    (assistant,) = [m for m in body["messages"] if m["role"] == "assistant"]
    assert (assistant["status"], assistant["error_code"]) == ("failed", "stopped")
    other.refresh_from_db()
    assert other.status == Message.Status.STREAMING  # only the read conversation is touched


def test_expire_streams_command(user: User, capsys: pytest.CaptureFixture[str]) -> None:
    """The command expires every stale answer and reports the count."""
    _streaming(user, age_s=settings.STREAM_LOCK_TTL_S + 5)
    call_command("expire_streams")
    assert "Expired 1 stale streaming answer(s)." in capsys.readouterr().out
