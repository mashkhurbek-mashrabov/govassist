from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import selectors, services
from apps.accounts.api.serializers import DeleteMeSerializer, MeSerializer, MeUpdateSerializer
from apps.accounts.models import User
from apps.chat.limits import QuotaService
from apps.common.i18n import resolve_lang


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfView(APIView):
    """Sets the ``csrftoken`` cookie; the SPA calls it once on boot."""

    permission_classes = [AllowAny]

    @extend_schema(summary="Set the CSRF cookie", responses={204: None})
    def get(self, request: Request) -> Response:
        """Return 204; the decorator sets the cookie.

        Args:
            request: The incoming request.
        """
        return Response(status=status.HTTP_204_NO_CONTENT)


def _me_response(request: Request, user: User) -> Response:
    """Serialize ``Me`` with its computed parts.

    Args:
        request: The current request (for language).
        user: The user to show.
    """
    context = {
        "lang": resolve_lang(request),
        "email_verified": selectors.is_email_verified(user),
        "quota": QuotaService().usage(user.id),
    }
    return Response(MeSerializer(user, context=context).data)


class MeView(APIView):
    """The signed-in user's profile."""

    @extend_schema(summary="Get my profile", responses=MeSerializer)
    def get(self, request: Request) -> Response:
        """Return ``Me``.

        Args:
            request: The incoming request.
        """
        return _me_response(request, request.user)  # type: ignore[arg-type]

    @extend_schema(summary="Update my profile", request=MeUpdateSerializer, responses=MeSerializer)
    def patch(self, request: Request) -> Response:
        """Update language, region/district or display name.

        Args:
            request: The incoming request.
        """
        user: User = request.user  # type: ignore[assignment]
        serializer = MeUpdateSerializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        services.update_profile(user, serializer.to_change())
        return _me_response(request, user)

    @extend_schema(
        summary="Delete my account",
        request=DeleteMeSerializer,
        responses={204: OpenApiResponse(description="Account and conversations deleted.")},
    )
    def delete(self, request: Request) -> Response:
        """Delete the account and all its conversations.

        Args:
            request: The incoming request.
        """
        DeleteMeSerializer(data=request.data).is_valid(raise_exception=True)
        services.delete_account(request.user)  # type: ignore[arg-type]
        return Response(status=status.HTTP_204_NO_CONTENT)
