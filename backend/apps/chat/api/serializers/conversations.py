from typing import Any

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.chat.api.serializers.messages import MESSAGE_SCHEMA, serialize_message
from apps.chat.models import Conversation


class ConversationSummarySerializer(serializers.ModelSerializer[Conversation]):
    """List item: title, last update and a short preview."""

    title = serializers.CharField()
    last_message_preview = serializers.CharField(allow_blank=True)

    class Meta:
        model = Conversation
        fields = ("id", "title", "updated_at", "last_message_preview")


class ConversationSerializer(serializers.ModelSerializer[Conversation]):
    """A conversation with all its messages, oldest first."""

    title = serializers.CharField()
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "title", "created_at", "updated_at", "messages")

    @extend_schema_field(serializers.ListField(child=MESSAGE_SCHEMA))
    def get_messages(self, obj: Conversation) -> list[dict[str, Any]]:
        """Messages oldest first, each in its role's shape.

        Args:
            obj: The conversation (messages prefetched with feedback).
        """
        return [serialize_message(message) for message in obj.messages.all()]
