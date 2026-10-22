from typing import Any

from django import forms
from django.http import HttpRequest

from apps.accounts import turnstile

TURNSTILE_TOKEN_MAX_LENGTH = 2048


class SignupForm(forms.Form):
    """Extra signup fields for allauth: a Turnstile token, checked before the account exists.

    allauth headless merges this form into its signup input (``ACCOUNT_SIGNUP_FORM_CLASS``).
    """

    turnstile_token = forms.CharField(max_length=TURNSTILE_TOKEN_MAX_LENGTH)

    def clean_turnstile_token(self) -> str:
        """Verify the token with Cloudflare.

        Returns:
            The valid token.

        Raises:
            forms.ValidationError: When Cloudflare rejects the token.
        """
        token: str = self.cleaned_data["turnstile_token"]
        if not turnstile.verify_turnstile(token):
            msg = "Bot check failed. Reload the page and try again."
            raise forms.ValidationError(msg, code="turnstile_failed")
        return token

    def signup(self, request: HttpRequest, user: Any) -> None:
        """Allauth hook after the user is created; nothing extra to store.

        Args:
            request: The signup request.
            user: The new user.
        """
