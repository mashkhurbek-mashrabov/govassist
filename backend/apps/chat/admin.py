from django.contrib import admin

from apps.chat.models import Conversation, Feedback, Message
from apps.common.admin import BaseAdmin


@admin.register(Conversation)
class ConversationAdmin(BaseAdmin):
    """Conversations (user text is already PII-scrubbed)."""

    list_select_related = ("user",)
    list_display = ("title", "user", "language", "updated_at")
    search_fields = ("title",)


@admin.register(Message)
class MessageAdmin(BaseAdmin):
    """Messages with run metadata for debugging and evaluation."""

    list_select_related = ("conversation",)
    list_display = (
        "conversation",
        "role",
        "status",
        "refused",
        "model",
        "latency_ms",
        "created_at",
    )
    list_filter = ("role", "status", "refused", "prompt_version")


@admin.register(Feedback)
class FeedbackAdmin(BaseAdmin):
    """Thumbs up/down from users."""

    list_select_related = ("message",)
    list_display = ("message", "rating", "created_at")
    list_filter = ("rating",)
