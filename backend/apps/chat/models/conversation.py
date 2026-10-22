from django.conf import settings
from django.db import models

from apps.common.constants import Lang
from apps.common.models import BaseModel


class Conversation(BaseModel):
    """A thread of questions and answers owned by one user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations"
    )
    title = models.CharField(max_length=120, blank=True)
    language = models.CharField(max_length=8, choices=Lang, default=Lang.UZ_LATN)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title or str(self.id)
