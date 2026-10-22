from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.i18n import resolve_lang
from apps.geo import selectors
from apps.geo.api.serializers import PlaceSerializer
from apps.geo.api.views.shared import LANG_PARAM, cached_get


@cached_get
class RegionListView(APIView):
    """Public list of regions with localized names."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="List regions", parameters=[LANG_PARAM], responses=PlaceSerializer(many=True)
    )
    def get(self, request: Request) -> Response:
        """Return all regions.

        Args:
            request: The incoming request.
        """
        data = PlaceSerializer(
            selectors.regions(), many=True, context={"lang": resolve_lang(request)}
        ).data
        return Response(data)
