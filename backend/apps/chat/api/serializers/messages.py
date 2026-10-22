from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from rest_framework import serializers

from apps.chat.api.serializers.feedback import FeedbackSerializer
from apps.chat.models import Message
from apps.chat.schemas import Answer, SourceList
from apps.offices.schemas import OfficeMatch


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
