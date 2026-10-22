from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from drf_spectacular.utils import OpenApiParameter

from apps.common.constants import Lang
from apps.geo.constants import GEO_CACHE_S

LANG_PARAM = OpenApiParameter("lang", str, enum=Lang.values, required=False)


cached_get = method_decorator(
    [cache_page(GEO_CACHE_S), vary_on_headers("Accept-Language", "Cookie")], name="get"
)
