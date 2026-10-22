from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


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
