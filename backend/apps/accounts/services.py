import urllib.parse
from dataclasses import dataclass

from allauth.account.models import EmailAddress
from allauth.core import context, ratelimit
from django.conf import settings
from django.db import transaction
from django.http import HttpRequest

from apps.accounts.constants import CONFIRM_EMAIL_ACTION
from apps.accounts.models import User
from apps.geo.models import District, Region


@dataclass(frozen=True, kw_only=True)
class ProfileUpdate:
    """Validated profile changes; ``None`` fields are left unchanged."""

    ui_language: str | None = None
    region: Region | None = None
    district: District | None = None
    display_name: str | None = None
    display_name_set: bool = False


def update_profile(user: User, change: ProfileUpdate) -> User:
    """Apply a validated profile change (the serializer keeps region and district consistent).

    Args:
        user: The user to update.
        change: Validated changes.

    Returns:
        The saved user.
    """
    if change.ui_language is not None:
        user.ui_language = change.ui_language
    if change.display_name_set:
        user.display_name = change.display_name or None
    if change.region is not None:
        user.region = change.region
    if change.district is not None:
        user.district = change.district
        user.region = change.district.region
    user.save()
    return user


@transaction.atomic
def delete_account(user: User) -> None:
    """Delete the user with all conversations, messages and feedback (cascade).

    Args:
        user: The user to delete.
    """
    user.delete()


def resend_verification(request: HttpRequest, email: str) -> None:
    """Queue a new verification email for ``email``, within allauth's per-email rate limit.

    The request does the same work for every email (one rate-limit check, one queued job):
    whether the account exists is decided later, in the task, so neither the answer nor its
    timing reveals it.

    Args:
        request: The current request (the rate limit is keyed on it and the email).
        email: The address typed by the user.
    """
    if not ratelimit.consume(request, action=CONFIRM_EMAIL_ACTION, key=email.lower()):
        return
    from apps.accounts.tasks import send_verification_email  # noqa: PLC0415 (tasks import services)

    send_verification_email.enqueue(email)


def send_verification_email(email: str) -> bool:
    """Send a verification link when ``email`` is an unverified address; else do nothing.

    Args:
        email: The address typed by the user.

    Returns:
        True when an email was sent.
    """
    address = EmailAddress.objects.filter(email__iexact=email, verified=False).first()
    if address is None:
        return False
    request = _site_request()
    with context.request_context(request):  # allauth reads the request from here too
        address.send_confirmation(request)
    return True


def _site_request() -> HttpRequest:
    """A minimal request for our own site, for emails sent outside a request (tasks).

    allauth names the site in emails from the request's host (``django.contrib.sites`` is
    not installed); the host is the one the links point to, ``FRONTEND_URL``.
    """
    parts = urllib.parse.urlsplit(settings.FRONTEND_URL)
    request = HttpRequest()
    request.META["HTTP_HOST"] = parts.netloc
    request.META["wsgi.url_scheme"] = parts.scheme
    return request
