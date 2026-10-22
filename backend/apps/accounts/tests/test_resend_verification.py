"""Tests for POST /api/v1/auth/resend-verification."""

import pytest
from django.core import mail
from rest_framework.test import APIClient

from conftest import make_user

pytestmark = pytest.mark.django_db
URL = "/api/v1/auth/resend-verification"


def test_unverified_address_gets_a_new_link(api: APIClient) -> None:
    """An unverified email receives a fresh verification link."""
    make_user("pending@example.com", verified=False)
    response = api.post(URL, {"email": "PENDING@example.com"})
    assert response.status_code == 204
    assert "/verify-email/" in str(mail.outbox[-1].body)


@pytest.mark.parametrize("email", ["nobody@example.com", "done@example.com"])
def test_unknown_or_verified_email_is_silent(api: APIClient, email: str) -> None:
    """Unknown and already verified emails get the same 204 and no email."""
    make_user("done@example.com", verified=True)
    assert api.post(URL, {"email": email}).status_code == 204
    assert not mail.outbox


def test_invalid_email_is_a_validation_error(api: APIClient) -> None:
    """Malformed input is rejected."""
    response = api.post(URL, {"email": "not-an-email"})
    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"


def test_rate_limited(api: APIClient) -> None:
    """After the hourly allowance (3/hour) the endpoint answers 429 with retry_after."""
    for _ in range(3):
        assert api.post(URL, {"email": "a@example.com"}).status_code == 204
    response = api.post(URL, {"email": "a@example.com"})
    assert response.status_code == 429
    assert response.json()["code"] == "rate_limited"
    assert response.json()["retry_after"] > 0
    assert response["Retry-After"]


@pytest.mark.parametrize("client_count", [2])
def test_rate_limit_is_per_real_client_ip(client_count: int) -> None:
    """Behind nginx, two clients get separate allowances (X-Real-IP from a trusted peer)."""
    from django.test import override_settings  # noqa: PLC0415

    with override_settings(TRUSTED_PROXY_NETWORKS=["172.16.0.0/12"]):
        for index in range(client_count):
            client = APIClient(REMOTE_ADDR="172.18.0.5", HTTP_X_REAL_IP=f"203.0.113.{index + 1}")
            statuses = [client.post(URL, {"email": "a@example.com"}).status_code for _ in range(4)]
            assert statuses == [204, 204, 204, 429]
