from django.db import models

from apps.chat.constants import FeedbackRating
from apps.chat.models.message import Message
from apps.common.models import BaseModel


class Feedback(BaseModel):
    """A thumbs up/down on an assistant message."""

    Rating = FeedbackRating

    message = models.OneToOneField(Message, on_delete=models.CASCADE, related_name="feedback")
    rating = models.SmallIntegerField(choices=Rating)
    comment = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.message_id}: {self.rating}"
