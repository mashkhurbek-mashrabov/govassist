from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from rest_framework import serializers

from apps.chat.models import Conversation, Feedback, Message
from apps.chat.schemas import Answer, SourceList
from apps.offices.schemas import OfficeMatch

FEEDBACK_COMMENT_MAX_CHARS = 1000


class FeedbackSerializer(serializers.ModelSerializer[Feedback]):
    """``Feedback``: thumbs up/down with an optional comment."""

    rating = serializers.ChoiceField(choices=Feedback.Rating.choices)
    comment = serializers.CharField(
        max_length=FEEDBACK_COMMENT_MAX_CHARS, required=False, allow_blank=True, default=""
    )

    class Meta:
        model = Feedback
        fields = ("rating", "comment")


class UserMessageSerializer(serializers.Serializer[Message]):
    """A user message (text is PII-scrubbed)."""

    id = serializers.UUIDField()
    role = serializers.CharField()
    text = serializers.CharField()
    created_at = serializers.DateTimeField()


class AssistantMessageSerializer(serializers.Serializer[Message]):
    """An assistant message: answer card, cited sources, office and status."""

    id = serializers.UUIDField()
    role = serializers.CharField()
    created_at = serializers.DateTimeField()
    status = serializers.ChoiceField(choices=Message.Status.choices)
    error_code = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()
    office = serializers.SerializerMethodField()
    refused = serializers.BooleanField()
    feedback = serializers.SerializerMethodField()

    def get_error_code(self, obj: Message) -> str | None:
        """The failure code, or null while streaming / on success.

        Args:
            obj: The message.
        """
        return obj.error_code or None

    @extend_schema_field(Answer)  # type: ignore[arg-type]  # pydantic model (spectacular contrib)
    def get_answer(self, obj: Message) -> dict[str, Any] | None:
        """The validated ``Answer`` or null.

        Args:
            obj: The message.
        """
        return obj.answer

    @extend_schema_field(SourceList)  # type: ignore[arg-type]  # pydantic model (spectacular contrib)
    def get_sources(self, obj: Message) -> list[dict[str, Any]]:
        """Cited sources in order of first citation.

        Args:
            obj: The message.
        """
        return list(obj.sources)

    @extend_schema_field(OfficeMatch)  # type: ignore[arg-type]  # pydantic model (spectacular contrib)
    def get_office(self, obj: Message) -> dict[str, Any] | None:
        """The ``OfficeMatch`` snapshot shown with the answer, or null.

        Args:
            obj: The message.
        """
        return obj.office_match

    @extend_schema_field(FeedbackSerializer(allow_null=True))
    def get_feedback(self, obj: Message) -> dict[str, Any] | None:
        """The user's feedback, or null.

        Args:
            obj: The message.
        """
        try:
            feedback = obj.feedback
        except ObjectDoesNotExist:
            return None
        return FeedbackSerializer(feedback).data


MESSAGE_SCHEMA = PolymorphicProxySerializer(
    component_name="Message",
    serializers=[UserMessageSerializer, AssistantMessageSerializer],
    resource_type_field_name="role",
    many=False,
)


def serialize_message(message: Message) -> dict[str, Any]:
    """Serialize a message with the serializer for its role.

    Args:
        message: A user or assistant message.
    """
    serializer = (
        UserMessageSerializer if message.role == Message.Role.USER else AssistantMessageSerializer
    )
    return serializer(message).data


class ConversationSummarySerializer(serializers.ModelSerializer[Conversation]):
    """List item: title, last update and a short preview."""

    last_message_preview = serializers.CharField(allow_blank=True)

    class Meta:
        model = Conversation
        fields = ("id", "title", "updated_at", "last_message_preview")


class ConversationSerializer(serializers.ModelSerializer[Conversation]):
    """A conversation with all its messages, oldest first."""

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
