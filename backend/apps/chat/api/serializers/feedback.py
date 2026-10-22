from rest_framework import serializers

from apps.chat.constants import FEEDBACK_COMMENT_MAX_CHARS
from apps.chat.models import Feedback


class FeedbackSerializer(serializers.ModelSerializer[Feedback]):
    """``Feedback``: thumbs up/down with an optional comment."""

    rating = serializers.ChoiceField(choices=Feedback.Rating.choices)
    comment = serializers.CharField(
        max_length=FEEDBACK_COMMENT_MAX_CHARS, required=False, allow_blank=True, default=""
    )

    class Meta:
        model = Feedback
        fields = ("rating", "comment")
