"""Loopback hosts are always allowed, so the container's own healthcheck passes."""

import importlib

import pytest
from django.test import Client

import config.settings.base as base_settings


def test_loopback_is_appended_to_configured_hosts(monkeypatch: pytest.MonkeyPatch) -> None:
    """A prod ALLOWED_HOSTS without 127.0.0.1 still gets the loopback hosts, without duplicates."""
    with monkeypatch.context() as patch:
        patch.setenv("ALLOWED_HOSTS", "govassist.example,localhost")
        reloaded = importlib.reload(base_settings)
        hosts = list(reloaded.ALLOWED_HOSTS)
    importlib.reload(base_settings)
    assert hosts == ["govassist.example", "localhost", "127.0.0.1"]


@pytest.mark.django_db
def test_healthcheck_host_is_accepted(client: Client) -> None:
    """The Dockerfile HEALTHCHECK request (Host 127.0.0.1) is not rejected with 400."""
    response = client.get("/api/v1/health", HTTP_HOST="127.0.0.1:8000")
    assert response.status_code == 200
