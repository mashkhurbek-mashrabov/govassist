from allauth.account.adapter import DefaultAccountAdapter
from django.http import HttpRequest

from apps.common.http import client_ip


class AccountAdapter(DefaultAccountAdapter):  # type: ignore[misc]
    """allauth adapter: its rate limits use the real client IP behind our nginx."""

    def get_client_ip(self, request: HttpRequest) -> str:
        """The client IP for allauth's login/signup/confirmation rate limits.

        Args:
            request: The current request.
        """
        return client_ip(request)
