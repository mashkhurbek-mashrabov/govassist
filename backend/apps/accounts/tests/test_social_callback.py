"""The OAuth provider callback is routable while allauth stays headless-only."""

import pytest
from django.test import Client
from django.urls import Resolver404, resolve

GOOGLE_CALLBACK = "/accounts/google/login/callback/"


def test_google_callback_resolves() -> None:
    """Google redirects here after consent; allauth's provider view must answer."""
    assert resolve(GOOGLE_CALLBACK).url_name == "google_callback"


@pytest.mark.parametrize("path", ["/accounts/login/", "/accounts/signup/", "/accounts/3rdparty/"])
def test_html_account_views_stay_off(path: str) -> None:
    """HEADLESS_ONLY keeps allauth's server-rendered pages unmounted."""
    with pytest.raises(Resolver404):
        resolve(path)


@pytest.mark.django_db
def test_callback_without_state_does_not_crash(client: Client) -> None:
    """A stray callback hit (no OAuth state) is handled by allauth, not a 500."""
    response = client.get(GOOGLE_CALLBACK)
    assert response.status_code < 500
