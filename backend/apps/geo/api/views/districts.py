from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.i18n import resolve_lang
from apps.geo import selectors
from apps.geo.api.serializers import PlaceSerializer
from apps.geo.api.views.shared import LANG_PARAM


class DistrictListView(APIView):
    """Public list of a region's districts with localized names."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="List districts of a region",
        parameters=[LANG_PARAM],
        responses=PlaceSerializer(many=True),
    )
    def get(self, request: Request, region_id: int) -> Response:
        """Return the districts of ``region_id``.

        Args:
            request: The incoming request.
            region_id: The region's SOATO code.

        Raises:
            NotFound: For an unknown region.
        """
        if not selectors.region_exists(region_id):
            raise NotFound
        return Response(selectors.district_places(region_id, resolve_lang(request)))
