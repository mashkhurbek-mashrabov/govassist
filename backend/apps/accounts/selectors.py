from allauth.account.models import EmailAddress

from apps.accounts.models import User


def is_email_verified(user: User) -> bool:
    """Return True when the user's login email is verified.

    Args:
        user: The user to check.
    """
    query = EmailAddress.objects.filter(user=user, email__iexact=user.email, verified=True)
    return bool(query.exists())


async def ais_email_verified(user: User) -> bool:
    """Async variant of :func:`is_email_verified` for the SSE view.

    Args:
        user: The user to check.
    """
    query = EmailAddress.objects.filter(user=user, email__iexact=user.email, verified=True)
    return bool(await query.aexists())
