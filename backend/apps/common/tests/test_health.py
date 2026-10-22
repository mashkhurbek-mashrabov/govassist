"""Tests for the health endpoint and request-id middleware."""

from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_health_ok(api: APIClient) -> None:
    """DB and cache up: 200 with both checks ok."""
    response = api.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"db": "ok", "redis": "ok"}}


def test_health_reports_failing_cache(api: APIClient) -> None:
    """A failing cache gives 503 and names the check."""
    with patch("apps.common.api.views.cache.set", side_effect=ConnectionError):
        response = api.get("/api/v1/health")
    assert response.status_code == 503
    assert response.json()["checks"] == {"db": "ok", "redis": "fail"}


def test_health_reports_failing_db(api: APIClient) -> None:
    """A failing database gives 503."""
    with patch("apps.common.api.views.connection.cursor", side_effect=ConnectionError):
        response = api.get("/api/v1/health")
    assert response.status_code == 503
    assert response.json()["checks"]["db"] == "fail"


def test_request_id_is_echoed(api: APIClient) -> None:
    """An incoming X-Request-ID is returned unchanged."""
    response = api.get("/api/v1/health", HTTP_X_REQUEST_ID="abc123")
    assert response["X-Request-ID"] == "abc123"


def test_request_id_is_generated(api: APIClient) -> None:
    """Without a header the middleware creates an id."""
    response = api.get("/api/v1/health")
    assert len(response["X-Request-ID"]) == 32
