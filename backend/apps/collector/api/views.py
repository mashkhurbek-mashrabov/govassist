from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.collector.api.serializers import SourceSummarySerializer
from apps.collector.selectors import public_sources


class SourceListView(APIView):
    """Public list of the sources behind the knowledge base."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="List knowledge sources",
        responses=inline_serializer(
            "SourceSummaryList", {"items": SourceSummarySerializer(many=True)}
        ),
    )
    def get(self, request: Request) -> Response:
        """Return approved, active sources with their counts.

        Args:
            request: The incoming request.
        """
        return Response({"items": SourceSummarySerializer(public_sources(), many=True).data})
