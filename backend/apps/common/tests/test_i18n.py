"""Tests for language resolution."""

from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.test import RequestFactory

from apps.accounts.models import User
from apps.common.i18n import Lang, resolve_lang


def _request(query: str = "", accept: str = "", user: User | None = None) -> HttpRequest:
    """Build a GET request with optional query, header and user."""
    request = RequestFactory().get(f"/x{query}", HTTP_ACCEPT_LANGUAGE=accept)
    request.user = user or AnonymousUser()
    return request


def test_query_param_wins() -> None:
    """``?lang=`` beats everything else."""
    assert resolve_lang(_request("?lang=ru", "en")) == Lang.RU


def test_user_language_beats_header() -> None:
    """A signed-in user's ui_language is used next."""
    user = User(email="a@example.com", ui_language=Lang.UZ_CYRL)
    assert resolve_lang(_request(accept="ru", user=user)) == Lang.UZ_CYRL


def test_accept_language_variants() -> None:
    """Accept-Language picks the first supported tag."""
    assert resolve_lang(_request(accept="fr, uz-Cyrl;q=0.9")) == Lang.UZ_CYRL
    assert resolve_lang(_request(accept="uz")) == Lang.UZ_LATN
    assert resolve_lang(_request(accept="en-GB")) == Lang.EN


def test_default_is_uzbek_latin() -> None:
    """Unknown or missing preferences fall back to uz-Latn."""
    assert resolve_lang(_request("?lang=de", "de")) == Lang.UZ_LATN
