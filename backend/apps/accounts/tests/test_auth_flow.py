"""End-to-end allauth headless flow: signup → verify email → login → profile."""

import re
from unittest.mock import patch
from urllib.parse import unquote

import pytest
from django.core import mail
from django.test import Client

from apps.geo.models import District

pytestmark = pytest.mark.django_db

AUTH = "/_allauth/browser/v1/auth"
PASSWORD = "a-long-enough-password"


def _signup(client: Client, *, turnstile_ok: bool = True) -> int:
    """Post the signup form with a patched Turnstile verdict; return the status code."""
    with patch("apps.accounts.turnstile.verify_turnstile", return_value=turnstile_ok):
        response = client.post(
            f"{AUTH}/signup",
            {"email": "new@example.com", "password": PASSWORD, "turnstile_token": "tok"},
            content_type="application/json",
        )
    return response.status_code


def _verification_key() -> str:
    """Extract the (URL-decoded) verification key from the email link."""
    match = re.search(r"/verify-email/(\S+)", str(mail.outbox[-1].body))
    assert match, mail.outbox[-1].body
    return unquote(match.group(1))


def test_signup_verify_login_and_set_profile(district: District) -> None:
    """The whole onboarding path works against the real allauth endpoints."""
    client = Client()
    assert _signup(client) == 401  # account created, email verification pending
    key = _verification_key()

    verify = client.post(f"{AUTH}/email/verify", {"key": key}, content_type="application/json")
    assert verify.status_code == 200

    client.logout()
    login = client.post(
        f"{AUTH}/login",
        {"email": "new@example.com", "password": PASSWORD},
        content_type="application/json",
    )
    assert login.status_code == 200

    me = client.get("/api/v1/me").json()
    assert me["email_verified"] is True
    assert me["profile_complete"] is False

    patched = client.patch(
        "/api/v1/me",
        {"region_id": district.region_id, "district_id": district.id},
        content_type="application/json",
    )
    assert patched.status_code == 200
    assert patched.json()["profile_complete"] is True


def test_signup_rejected_when_turnstile_fails() -> None:
    """A failed bot check blocks account creation."""
    assert _signup(Client(), turnstile_ok=False) == 400
    assert not mail.outbox


def test_email_links_point_at_spa() -> None:
    """Verification emails link to the SPA route from the contract."""
    _signup(Client())
    assert "http://localhost:5173/verify-email/" in mail.outbox[-1].body
