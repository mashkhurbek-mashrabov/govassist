from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.constants import Lang
from apps.common.i18n import resolve_lang
from apps.geo import selectors
from apps.geo.api.serializers import PlaceSerializer
from apps.geo.constants import GEO_CACHE_S

LANG_PARAM = OpenApiParameter("lang", str, enum=Lang.values, required=False)
_cached = method_decorator(
    [cache_page(GEO_CACHE_S), vary_on_headers("Accept-Language", "Cookie")], name="get"
)


@_cached
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


@_cached
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
        data = PlaceSerializer(
            selectors.districts_of(region_id), many=True, context={"lang": resolve_lang(request)}
        ).data
        return Response(data)
