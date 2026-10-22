"""DRF throttles keyed by the real client IP (see ``apps.common.http.client_ip``)."""

from rest_framework import throttling
from rest_framework.request import Request

from apps.common.http import client_ip


class AnonRateThrottle(throttling.AnonRateThrottle):
    """Anonymous rate limit per real client IP."""

    def get_ident(self, request: Request) -> str:
        """The client IP behind our proxy.

        Args:
            request: The DRF request.
        """
        return client_ip(request._request)


class UserRateThrottle(throttling.UserRateThrottle):
    """Per-user rate limit; anonymous requests fall back to the real client IP."""

    def get_ident(self, request: Request) -> str:
        """The client IP behind our proxy.

        Args:
            request: The DRF request.
        """
        return client_ip(request._request)


class ScopedRateThrottle(throttling.ScopedRateThrottle):
    """Scoped rate limit (``throttle_scope``) per user or real client IP."""

    def get_ident(self, request: Request) -> str:
        """The client IP behind our proxy.

        Args:
            request: The DRF request.
        """
        return client_ip(request._request)
