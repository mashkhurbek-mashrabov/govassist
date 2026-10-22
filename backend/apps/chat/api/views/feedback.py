from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.chat import selectors, services
from apps.chat.api.serializers import FeedbackSerializer


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
