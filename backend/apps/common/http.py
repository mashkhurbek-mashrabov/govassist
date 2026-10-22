"""The real client IP behind exactly one trusted proxy hop (our nginx)."""

import ipaddress
from functools import cache

from django.conf import settings
from django.http import HttpRequest

from apps.common.constants import CLIENT_IP_HEADER

type Network = ipaddress.IPv4Network | ipaddress.IPv6Network


@cache
def _trusted_networks(networks: tuple[str, ...]) -> tuple[Network, ...]:
    """Parse ``TRUSTED_PROXY_NETWORKS`` once."""
    return tuple(ipaddress.ip_network(network) for network in networks)


def _parse(value: str) -> str | None:
    """A normalized IP address, or None when ``value`` is not one."""
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None


def client_ip(request: HttpRequest) -> str:
    """The client IP for rate limits.

    ``X-Real-IP`` is used only when the direct peer (``REMOTE_ADDR``) is inside
    ``TRUSTED_PROXY_NETWORKS`` (our nginx); a header sent by anyone else is ignored, so it
    cannot be spoofed by talking to the backend directly.

    Args:
        request: The current request.
    """
    peer = _parse(request.META.get("REMOTE_ADDR", "")) or ""
    trusted = _trusted_networks(tuple(settings.TRUSTED_PROXY_NETWORKS))
    if peer and any(ipaddress.ip_address(peer) in network for network in trusted):
        forwarded = _parse(request.headers.get(CLIENT_IP_HEADER, ""))
        if forwarded:
            return forwarded
    return peer
