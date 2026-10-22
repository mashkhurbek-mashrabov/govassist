"""API tests for conversations, feedback and suggestions."""

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.chat.models import Conversation, Feedback, Message
from conftest import make_user

pytestmark = pytest.mark.django_db


def _conversation(user: User, title: str = "NAMUNA") -> tuple[Conversation, Message]:
    """A conversation with one question and one failed (stopped) answer."""
    conversation = Conversation.objects.create(user=user, title=title)
    Message.objects.create(conversation=conversation, role="user", text="NAMUNA savol [PHONE]")
    answer = Message.objects.create(
        conversation=conversation, role="assistant", status="failed", error_code="stopped"
    )
    return conversation, answer


def test_list_is_paginated_newest_first(auth_api: APIClient, user: User) -> None:
    """Cursor pagination with the contract envelope and a preview of the last question."""
    for index in range(3):
        _conversation(user, title=f"NAMUNA {index}")
    _conversation(make_user("other@example.com"), title="not mine")
    page = auth_api.get("/api/v1/conversations?limit=2").json()
    assert [item["title"] for item in page["results"]] == ["NAMUNA 2", "NAMUNA 1"]
    assert page["results"][0]["last_message_preview"] == "NAMUNA savol [PHONE]"
    assert page["next"]
    rest = auth_api.get(f"/api/v1/conversations?limit=2&cursor={page['next']}").json()
    assert [item["title"] for item in rest["results"]] == ["NAMUNA 0"]
    assert rest["next"] is None


def test_detail_shows_both_message_shapes(auth_api: APIClient, user: User) -> None:
    """User and assistant messages follow their contract shapes, incl. error_code."""
    conversation, _ = _conversation(user)
    messages = auth_api.get(f"/api/v1/conversations/{conversation.id}").json()["messages"]
    assert set(messages[0]) == {"id", "role", "text", "created_at"}
    assert messages[1]["status"] == "failed"
    assert messages[1]["error_code"] == "stopped"
    assert messages[1]["answer"] is None
    assert messages[1]["created_at"].endswith("Z")


def test_others_conversations_are_404(auth_api: APIClient) -> None:
    """Not your conversation: not_found."""
    conversation, _ = _conversation(make_user("other@example.com"))
    assert auth_api.get(f"/api/v1/conversations/{conversation.id}").status_code == 404
    assert auth_api.delete(f"/api/v1/conversations/{conversation.id}").status_code == 404


def test_delete(auth_api: APIClient, user: User) -> None:
    """Deleting removes the conversation and its messages."""
    conversation, _ = _conversation(user)
    assert auth_api.delete(f"/api/v1/conversations/{conversation.id}").status_code == 204
    assert not Message.objects.exists()


def test_feedback_create_then_update(auth_api: APIClient, user: User) -> None:
    """201 on create, 200 on update; detail shows the feedback."""
    conversation, answer = _conversation(user)
    url = f"/api/v1/messages/{answer.id}/feedback"
    created = auth_api.post(url, {"rating": 1})
    assert (created.status_code, created.json()) == (201, {"rating": 1, "comment": ""})
    updated = auth_api.post(url, {"rating": -1, "comment": "NAMUNA"})
    assert (updated.status_code, updated.json()) == (200, {"rating": -1, "comment": "NAMUNA"})
    assert Feedback.objects.count() == 1
    detail = auth_api.get(f"/api/v1/conversations/{conversation.id}").json()
    assert detail["messages"][1]["feedback"] == {"rating": -1, "comment": "NAMUNA"}


def test_feedback_validation_and_ownership(auth_api: APIClient, user: User) -> None:
    """Bad ratings are 400; user messages and others' answers are 404."""
    _, answer = _conversation(user)
    assert auth_api.post(f"/api/v1/messages/{answer.id}/feedback", {"rating": 2}).status_code == 400
    too_long = {"rating": 1, "comment": "x" * 1001}
    assert auth_api.post(f"/api/v1/messages/{answer.id}/feedback", too_long).status_code == 400
    question = Message.objects.get(role="user")
    assert (
        auth_api.post(f"/api/v1/messages/{question.id}/feedback", {"rating": 1}).status_code == 404
    )
    _, foreign = _conversation(make_user("other@example.com"))
    assert (
        auth_api.post(f"/api/v1/messages/{foreign.id}/feedback", {"rating": 1}).status_code == 404
    )


@pytest.mark.parametrize(("lang", "first"), [("ru", "Как заменить паспорт?"), ("xx", None)])
def test_suggestions_follow_ui_language(
    auth_api: APIClient, user: User, lang: str, first: str | None
) -> None:
    """At most six suggestions in the UI language (uz-Latn fallback)."""
    user.ui_language = lang
    user.save()
    items = auth_api.get("/api/v1/suggestions").json()["items"]
    assert len(items) == 6
    assert items[0]["text"] == (first or "Pasportimni qanday almashtiraman?")
    assert set(items[0]) == {"text", "category"}


def test_chat_endpoints_need_login(api: APIClient) -> None:
    """Every chat read endpoint is 401 for anonymous users."""
    for url in ("/api/v1/conversations", "/api/v1/suggestions"):
        assert api.get(url).status_code == 401
