from uuid import UUID

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat import selectors, services
from apps.chat.api.serializers import ConversationSerializer, ConversationSummarySerializer
from apps.chat.models import Conversation
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
        """Load the user's conversation or raise 404 (dead ``streaming`` answers expired first)."""
        services.expire_stale_streams(conversation_id=conversation_id)
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
