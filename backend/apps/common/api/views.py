import logging

from django.core.cache import cache
from django.db import connection
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

HEALTH_CACHE_KEY = "health:ping"
OK = "ok"
FAIL = "fail"


def _check_db() -> str:
    """Return ``ok`` when the database answers a trivial query."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        logger.exception("Health check: database failed")
        return FAIL
    return OK


def _check_cache() -> str:
    """Return ``ok`` when the cache (Redis) round-trips a value."""
    try:
        cache.set(HEALTH_CACHE_KEY, OK, timeout=5)
        healthy = cache.get(HEALTH_CACHE_KEY) == OK
    except Exception:
        logger.exception("Health check: cache failed")
        return FAIL
    return OK if healthy else FAIL


_health_schema = inline_serializer(
    "Health",
    {
        "status": serializers.CharField(),
        "checks": serializers.DictField(child=serializers.CharField()),
    },
)


class HealthView(APIView):
    """Liveness/readiness probe for Docker and the load balancer."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    @extend_schema(
        summary="Health check",
        responses={200: _health_schema, 503: OpenApiResponse(_health_schema)},
    )
    def get(self, request: Request) -> Response:
        """Report database and Redis status.

        Args:
            request: The incoming request.

        Returns:
            200 when all checks pass, else 503 with the failing checks.
        """
        checks = {"db": _check_db(), "redis": _check_cache()}
        healthy = all(value == OK for value in checks.values())
        return Response(
            {"status": OK if healthy else FAIL, "checks": checks},
            status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
