from drf_spectacular.utils import OpenApiParameter

from apps.common.constants import Lang

LANG_PARAM = OpenApiParameter("lang", str, enum=Lang.values, required=False)
