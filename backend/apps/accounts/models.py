from typing import Any, ClassVar

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from apps.common.i18n import Lang
from apps.common.models import BaseModel


class UserManager(BaseUserManager["User"]):
    """Manager for the email-login user (no username)."""

    use_in_migrations = True

    def create_user(self, email: str, password: str | None = None, **extra: Any) -> User:
        """Create a regular user.

        Args:
            email: Login email.
            password: Raw password, or None for an unusable password.
            **extra: Other model fields.

        Returns:
            The saved user.

        Raises:
            ValueError: When the email is empty.
        """
        if not email:
            msg = "Email is required."
            raise ValueError(msg)
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra: Any) -> User:
        """Create a staff superuser.

        Args:
            email: Login email.
            password: Raw password.
            **extra: Other model fields.

        Returns:
            The saved superuser.
        """
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)


class User(BaseModel, AbstractUser):
    """A citizen account. Logs in with email; region/district drive office lookup."""

    username = None  # type: ignore[assignment]
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=80, null=True, blank=True)  # noqa: DJ001
    ui_language = models.CharField(max_length=8, choices=Lang, default=Lang.UZ_LATN)
    region = models.ForeignKey(
        "geo.Region", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    district = models.ForeignKey(
        "geo.District", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    objects: ClassVar[UserManager] = UserManager()  # type: ignore[assignment]

    def __str__(self) -> str:
        return self.email

    @property
    def profile_complete(self) -> bool:
        """True once the user has chosen a region and a district."""
        return self.region_id is not None and self.district_id is not None
