"""Background jobs for accounts (run by ``db_worker``)."""

from django.tasks import task

from apps.accounts import services


@task
def send_verification_email(email: str) -> bool:
    """Send a new verification link to ``email`` when it is an unverified address.

    Runs outside the request, so how long the lookup and sending take never shows in the
    API response time.

    Args:
        email: The address the user typed.

    Returns:
        True when an email was sent.
    """
    return services.send_verification_email(email)
