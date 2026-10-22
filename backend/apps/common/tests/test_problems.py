"""Tests for problem+json rendering."""

from typing import Any

import pytest
from django.http import Http404
from rest_framework import exceptions

from apps.common.problems import (
    PROBLEM_CONTENT_TYPE,
    QuotaExceeded,
    RateLimited,
    exception_handler,
    problem_response,
)

CASES: list[tuple[Exception, int, str]] = [
    (exceptions.NotAuthenticated(), 401, "not_authenticated"),
    (exceptions.ValidationError({"text": ["Required."]}), 400, "validation_error"),
    (exceptions.Throttled(wait=12), 429, "rate_limited"),
    (exceptions.NotFound(), 404, "not_found"),
    (Http404(), 404, "not_found"),
    (exceptions.PermissionDenied(), 403, "permission_denied"),
    (exceptions.MethodNotAllowed("PUT"), 405, "method_not_allowed"),
    (QuotaExceeded(), 429, "quota_exceeded"),
    (RuntimeError("boom"), 500, "internal_error"),
]


@pytest.mark.parametrize(("exc", "status", "code"), CASES)
def test_exception_handler_maps_to_contract_codes(exc: Exception, status: int, code: str) -> None:
    """Every exception becomes problem+json with the contract code and status."""
    response = exception_handler(exc, {})
    body: dict[str, Any] = response.data
    assert response.status_code == status
    assert response.content_type == PROBLEM_CONTENT_TYPE
    assert body["code"] == code
    assert body["status"] == status
    assert body["type"] == "about:blank"
    assert {"title", "detail", "errors"} <= body.keys()


def test_validation_errors_are_listed_per_field() -> None:
    """Field errors land in ``errors``."""
    response = exception_handler(exceptions.ValidationError({"text": ["Required."]}), {})
    assert response.data["errors"] == {"text": ["Required."]}


def test_list_validation_error_goes_to_non_field_errors() -> None:
    """A bare list error is wrapped under ``non_field_errors``."""
    response = exception_handler(exceptions.ValidationError(["Bad."]), {})
    assert response.data["errors"] == {"non_field_errors": ["Bad."]}


def test_throttled_sets_retry_after_header() -> None:
    """Throttling exposes ``retry_after`` in body and header."""
    response = exception_handler(exceptions.Throttled(wait=12), {})
    assert response.data["retry_after"] == 12
    assert response["Retry-After"] == "12"


def test_problem_response_for_plain_views() -> None:
    """The async view helper renders the same shape."""
    response = problem_response(RateLimited("Hourly question limit reached.", retry_after=60))
    assert response.status_code == 429
    assert response["Content-Type"] == PROBLEM_CONTENT_TYPE
    assert response["Retry-After"] == "60"
    assert b'"code": "rate_limited"' in response.content
