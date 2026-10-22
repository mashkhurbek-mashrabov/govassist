from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.chat.suggestions import suggestions_for

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
