from uuid import UUID

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.chat import selectors, services
from apps.chat.api.serializers import (
    ConversationSerializer,
    ConversationSummarySerializer,
    FeedbackSerializer,
)
from apps.chat.models import Conversation
from apps.chat.suggestions import suggestions_for
from apps.common.pagination import ContractCursorPagination


class ConversationListView(ListAPIView[Conversation]):
    """The user's conversations, newest first, cursor-paginated."""

    serializer_class = ConversationSummarySerializer
    pagination_class = ContractCursorPagination

    def get_queryset(self):  # type: ignore[no-untyped-def]  # noqa: ANN201
        """Only the signed-in user's conversations."""
        return selectors.conversations_of(self.request.user)  # type: ignore[arg-type]

    @extend_schema(
        summary="List my conversations",
        parameters=[
            OpenApiParameter("cursor", str, required=False),
            OpenApiParameter("limit", int, required=False),
        ],
    )
    def get(self, request: Request) -> Response:
        """Return one page of conversations.

        Args:
            request: The incoming request.
        """
        return super().get(request)


class ConversationDetailView(APIView):
    """One conversation with its messages; delete removes it."""

    def _conversation(self, request: Request, conversation_id: UUID) -> Conversation:
        """Load the user's conversation or raise 404."""
        conversation = selectors.conversation_with_messages(request.user, conversation_id)  # type: ignore[arg-type]
        if conversation is None:
            raise NotFound
        return conversation

    @extend_schema(summary="Get a conversation", responses=ConversationSerializer)
    def get(self, request: Request, conversation_id: UUID) -> Response:
        """Return the conversation with all messages.

        Args:
            request: The incoming request.
            conversation_id: The conversation id.
        """
        return Response(ConversationSerializer(self._conversation(request, conversation_id)).data)

    @extend_schema(summary="Delete a conversation", responses={204: None})
    def delete(self, request: Request, conversation_id: UUID) -> Response:
        """Delete the conversation and everything in it.

        Args:
            request: The incoming request.
            conversation_id: The conversation id.
        """
        services.delete_conversation(self._conversation(request, conversation_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


class FeedbackView(APIView):
    """Thumbs up/down on an assistant message (upsert)."""

    @extend_schema(
        summary="Rate an answer",
        request=FeedbackSerializer,
        responses={200: FeedbackSerializer, 201: FeedbackSerializer},
    )
    def post(self, request: Request, message_id: UUID) -> Response:
        """Create (201) or update (200) the feedback.

        Args:
            request: The incoming request.
            message_id: The assistant message id.
        """
        user: User = request.user  # type: ignore[assignment]
        message = selectors.assistant_message_of(user, message_id)
        if message is None:
            raise NotFound
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feedback, created = services.upsert_feedback(message, **serializer.validated_data)
        return Response(
            FeedbackSerializer(feedback).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


_suggestions_schema = inline_serializer(
    "Suggestions",
    {
        "items": inline_serializer(
            "Suggestion",
            {"text": serializers.CharField(), "category": serializers.CharField()},
            many=True,
        )
    },
)


class SuggestionsView(APIView):
    """Starter questions in the user's UI language."""

    @extend_schema(
        summary="Starter questions", responses={200: OpenApiResponse(_suggestions_schema)}
    )
    def get(self, request: Request) -> Response:
        """Return at most six suggestions.

        Args:
            request: The incoming request.
        """
        user: User = request.user  # type: ignore[assignment]
        return Response({"items": suggestions_for(user.ui_language)})
