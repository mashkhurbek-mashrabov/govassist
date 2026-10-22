from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import services
from apps.accounts.api.serializers import ResendVerificationSerializer
from apps.common.throttling import ScopedRateThrottle


class ResendVerificationView(APIView):
    """Resend the verification email; always 204 so accounts can't be enumerated."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "resend_verification"

    @extend_schema(
        summary="Resend the verification email",
        request=ResendVerificationSerializer,
        responses={204: OpenApiResponse(description="Always, whether or not the email exists.")},
    )
    def post(self, request: Request) -> Response:
        """Validate the email and send a new link when it is unverified.

        Args:
            request: The incoming request.
        """
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.resend_verification(request._request, serializer.validated_data["email"])
        return Response(status=status.HTTP_204_NO_CONTENT)
