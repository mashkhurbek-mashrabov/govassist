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
    assert "http://localhost:5173/forgot-password" in str(mail.outbox[-1].body)


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


def _post(client: Client, path: str, body: dict[str, Any]) -> Any:
    """POST JSON to an allauth headless endpoint."""
    return client.post(f"/_allauth/browser/v1{path}", body, content_type="application/json")


def test_key_and_password_codes() -> None:
    """Codes the SPA maps (contract v1.8): verify/reset keys and password change."""
    client = Client()
    verify = _post(client, "/auth/email/verify", {"key": "nope"})
    assert _codes(verify.json()["errors"]) == {("invalid_or_expired_key", "key")}
    reset = _post(
        client, "/auth/password/reset", {"key": "nope", "password": "a-long-enough-password"}
    )
    assert _codes(reset.json()["errors"]) == {("invalid_password_reset", "key")}
    unknown = _post(client, "/auth/password/request", {"email": "nobody@example.com"})
    assert unknown.status_code == 200  # no account enumeration

    make_user("pw@example.com")
    _post(
        client,
        "/auth/login",
        {"email": "pw@example.com", "password": "correct-horse-battery-staple"},
    )
    wrong = _post(
        client,
        "/account/password/change",
        {"current_password": "wrong-password", "new_password": "another-long-password"},
    )
    assert _codes(wrong.json()["errors"]) == {("enter_current_password", "current_password")}
    missing = _post(client, "/account/password/change", {"new_password": "another-long-password"})
    assert _codes(missing.json()["errors"]) == {("required", "current_password")}


def test_generic_field_codes_and_unverified_login() -> None:
    """Field validation uses Django's generic codes; unverified login is a pending flow."""
    with patch("apps.accounts.turnstile.verify_turnstile", return_value=True):
        bad_email = _post(
            Client(),
            "/auth/signup",
            {"email": "bad", "password": "a-long-enough-password", "turnstile_token": "t"},
        )
    assert ("invalid", "email") in _codes(bad_email.json()["errors"])
    make_user("unv@example.com", verified=False)
    pending = _post(
        Client(),
        "/auth/login",
        {"email": "unv@example.com", "password": "correct-horse-battery-staple"},
    )
    assert pending.status_code == 401
    flows = {flow["id"]: flow for flow in pending.json()["data"]["flows"]}
    assert flows["verify_email"]["is_pending"] is True
