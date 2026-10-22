from rest_framework import exceptions
from rest_framework.authentication import SessionAuthentication
from rest_framework.request import Request

from apps.common.problems import CsrfFailed


class CsrfProblemSessionAuthentication(SessionAuthentication):
    """Session auth whose CSRF failures are ``csrf_failed`` problems, not generic 403s."""

    def enforce_csrf(self, request: Request) -> None:
        """Run DRF's CSRF check, re-raising its failure with the contract code.

        Args:
            request: The DRF request.

        Raises:
            CsrfFailed: When the CSRF token is missing or wrong.
        """
        try:
            super().enforce_csrf(request)
        except exceptions.PermissionDenied as exc:
            raise CsrfFailed from exc
