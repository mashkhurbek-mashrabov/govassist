"""Tests for the real client IP behind one trusted proxy hop."""

import pytest
from django.http import HttpRequest
from django.test import RequestFactory, override_settings
from rest_framework.request import Request

from apps.accounts.adapter import AccountAdapter
from apps.common.http import client_ip
from apps.common.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle

NGINX = "172.18.0.5"
CLIENT = "203.0.113.7"


def _request(peer: str, real_ip: str | None = None) -> HttpRequest:
    """A request from ``peer`` that may carry X-Real-IP."""
    headers = {"X-Real-IP": real_ip} if real_ip else {}
    return RequestFactory().get("/", REMOTE_ADDR=peer, headers=headers)


@override_settings(TRUSTED_PROXY_NETWORKS=["172.16.0.0/12"])
def test_trusted_proxy_header_is_used() -> None:
    """Behind nginx the X-Real-IP value is the client."""
    assert client_ip(_request(NGINX, CLIENT)) == CLIENT


@override_settings(TRUSTED_PROXY_NETWORKS=["172.16.0.0/12"])
def test_header_from_untrusted_peer_is_ignored() -> None:
    """A direct caller cannot spoof its IP with X-Real-IP."""
    assert client_ip(_request(CLIENT, "1.2.3.4")) == CLIENT


@override_settings(TRUSTED_PROXY_NETWORKS=[])
def test_no_trusted_proxies_means_remote_addr() -> None:
    """With nothing trusted (dev default) the peer address is used."""
    assert client_ip(_request(NGINX, CLIENT)) == NGINX


@override_settings(TRUSTED_PROXY_NETWORKS=["172.16.0.0/12"])
def test_invalid_header_falls_back_to_peer() -> None:
    """A malformed X-Real-IP is ignored."""
    assert client_ip(_request(NGINX, "not-an-ip")) == NGINX


@override_settings(TRUSTED_PROXY_NETWORKS=["172.16.0.0/12"])
@pytest.mark.parametrize("throttle", [AnonRateThrottle, UserRateThrottle, ScopedRateThrottle])
def test_drf_throttles_and_allauth_use_the_real_ip(throttle: type) -> None:
    """DRF throttles and allauth's rate limits key on the same client IP."""
    django_request = _request(NGINX, CLIENT)
    assert throttle().get_ident(Request(django_request)) == CLIENT
    assert AccountAdapter().get_client_ip(django_request) == CLIENT
