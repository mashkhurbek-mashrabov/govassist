"""Pin the allauth/Django error codes the SPA maps (contract §2 "Auth errors")."""

from typing import Any
from unittest.mock import patch

import pytest
from django.core import mail
from django.test import Client

from conftest import make_user

pytestmark = pytest.mark.django_db
AUTH = "/_allauth/browser/v1/auth"


def _signup(body: dict[str, Any], *, turnstile_ok: bool = True) -> list[dict[str, Any]]:
    """Post a signup and return the allauth error list."""
    with patch("apps.accounts.turnstile.verify_turnstile", return_value=turnstile_ok):
        response = Client().post(f"{AUTH}/signup", body, content_type="application/json")
    assert response.status_code == 400, response.content
    errors: list[dict[str, Any]] = response.json()["errors"]
    return errors


def _codes(errors: list[dict[str, Any]]) -> set[tuple[str, str | None]]:
    """(code, param) pairs of an error list."""
    return {(error["code"], error.get("param")) for error in errors}


@pytest.mark.parametrize(
    ("body", "turnstile_ok"),
    [
        ({"email": "a@example.com", "password": "a-long-enough-password"}, True),
        (
            {
                "email": "a@example.com",
                "password": "a-long-enough-password",
                "turnstile_token": "t",
            },
            False,
        ),
    ],
)
def test_turnstile_failed(body: dict[str, Any], turnstile_ok: bool) -> None:
    """Missing or rejected tokens give turnstile_failed on turnstile_token."""
    assert _codes(_signup(body, turnstile_ok=turnstile_ok)) == {
        ("turnstile_failed", "turnstile_token")
    }


def test_existing_email_is_not_revealed() -> None:
    """Enumeration prevention: an existing email looks like a fresh signup (no email_taken).

    The owner gets an "account already exists" email with a reset link instead.
    """
    make_user("taken@example.com")
    body = {
        "email": "taken@example.com",
        "password": "a-long-enough-password",
        "turnstile_token": "t",
    }
    with patch("apps.accounts.turnstile.verify_turnstile", return_value=True):
        response = Client().post(f"{AUTH}/signup", body, content_type="application/json")
    assert response.status_code == 401
    assert "http://localhost:5173/reset-password" in str(mail.outbox[-1].body)


@pytest.mark.parametrize(
    ("password", "codes"),
    [
        ("short1", {"password_too_short", "password_too_common"}),
        ("zq7#Lm2", {"password_too_short"}),
        ("1234567890123", {"password_entirely_numeric", "password_too_common"}),
        ("password1234", {"password_too_common"}),
    ],
)
def test_password_validator_codes(password: str, codes: set[str]) -> None:
    """Django's validators surface their codes on ``password``."""
    body = {"email": "similar.user@example.com", "password": password, "turnstile_token": "t"}
    found = _codes(_signup(body))
    assert {code for code, _ in found} == codes
    assert {param for _, param in found} == {"password"}


def test_login_mismatch_and_rate_limit() -> None:
    """Wrong password is email_password_mismatch; repeats hit too_many_login_attempts."""
    make_user("login@example.com")
    client = Client()
    codes = []
    for _ in range(6):
        response = client.post(
            f"{AUTH}/login",
            {"email": "login@example.com", "password": "wrong-password"},
            content_type="application/json",
        )
        codes.append(response.json()["errors"][0]["code"])
    assert codes[0] == "email_password_mismatch"
    assert codes[-1] == "too_many_login_attempts"
