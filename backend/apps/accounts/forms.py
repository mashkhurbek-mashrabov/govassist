from typing import Any

from django import forms
from django.http import HttpRequest

from apps.accounts import turnstile
from apps.accounts.constants import TURNSTILE_FAILED, TURNSTILE_MESSAGE, TURNSTILE_TOKEN_MAX_LENGTH


class SignupForm(forms.Form):
    """Extra signup fields for allauth: a Turnstile token, checked before the account exists.

    allauth headless merges this form into its signup input (``ACCOUNT_SIGNUP_FORM_CLASS``).
    """

    turnstile_token = forms.CharField(
        max_length=TURNSTILE_TOKEN_MAX_LENGTH,
        required=False,
        error_messages={"max_length": TURNSTILE_MESSAGE},
    )

    def clean_turnstile_token(self) -> str:
        """Verify the token with Cloudflare.

        A missing token fails the same way, so the SPA handles one code (contract §2).

        Returns:
            The valid token.

        Raises:
            forms.ValidationError: ``turnstile_failed`` when the token is missing or rejected.
        """
        token: str = self.cleaned_data.get("turnstile_token") or ""
        if not token or not turnstile.verify_turnstile(token):
            raise forms.ValidationError(TURNSTILE_MESSAGE, code=TURNSTILE_FAILED)
        return token

    def signup(self, request: HttpRequest, user: Any) -> None:
        """Allauth hook after the user is created; nothing extra to store.

        Args:
            request: The signup request.
            user: The new user.
        """
