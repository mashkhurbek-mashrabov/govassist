from dataclasses import dataclass

from django.db import transaction

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
    """Apply a profile change and keep region/district consistent.

    When only the region changes and the old district belongs elsewhere, the district is
    cleared so the user must pick one again.

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
        if change.district is None and user.district and user.district.region_id != user.region_id:
            user.district = None
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
