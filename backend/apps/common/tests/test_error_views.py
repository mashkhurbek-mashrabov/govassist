"""Every API error is problem+json: CSRF failures, unknown URLs and crashes."""

import pytest
from django.test import Client, RequestFactory
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.common.views import csrf_failure, not_found, server_error

pytestmark = pytest.mark.django_db


def test_drf_csrf_failure_is_csrf_failed(user: User) -> None:
    """A logged-in PATCH without the token is a csrf_failed problem."""
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(user)
    response = client.patch("/api/v1/me", {"ui_language": "ru"}, format="json")
    assert response.status_code == 403
    assert response["Content-Type"] == "application/problem+json"
    assert response.json()["code"] == "csrf_failed"


def test_middleware_csrf_failure_on_chat_is_csrf_failed(user: User) -> None:
    """The plain Django chat view gets the same problem from CSRF_FAILURE_VIEW."""
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    response = client.post("/api/v1/chat", {"text": "x"}, content_type="application/json")
    assert response.status_code == 403
    assert response.json()["code"] == "csrf_failed"


@pytest.mark.parametrize(
    "path",
    ["/api/v1/conversations/not-a-uuid", "/api/v1/nope", "/api/v1/messages/x/feedback"],
)
def test_unknown_api_urls_are_problem_json(api: APIClient, path: str) -> None:
    """Unknown API paths are not_found problems, never Django HTML."""
    response = api.get(path)
    assert response.status_code == 404
    assert response["Content-Type"] == "application/problem+json"
    assert response.json()["code"] == "not_found"


def test_error_views_fall_back_to_html_outside_the_api() -> None:
    """Non-API paths keep Django's normal pages."""
    factory = RequestFactory()
    assert csrf_failure(factory.post("/admin/login/")).status_code == 403
    assert b"problem" not in not_found(factory.get("/x"), Exception()).content
    assert server_error(factory.get("/x")).status_code == 500
    api_500 = server_error(factory.get("/api/v1/x"))
    assert api_500["Content-Type"] == "application/problem+json"
