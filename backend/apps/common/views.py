"""Error views that keep every API error in problem+json (contract §1)."""

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import defaults
from django.views.csrf import csrf_failure as django_csrf_failure

from apps.common.problems import PROBLEM_CONTENT_TYPE, problem_body

API_PREFIXES = ("/api/", "/_allauth/")
CSRF_DETAIL = "CSRF check failed. Reload the page and try again."


def is_api(request: HttpRequest) -> bool:
    """True for API and headless-auth paths (the SPA reads JSON there)."""
    return request.path.startswith(API_PREFIXES)


def _problem(status: int, code: str, detail: str) -> JsonResponse:
    """A problem+json response."""
    return JsonResponse(
        problem_body(status, code, detail), status=status, content_type=PROBLEM_CONTENT_TYPE
    )


def csrf_failure(request: HttpRequest, reason: str = "") -> HttpResponse:
    """``CSRF_FAILURE_VIEW``: ``csrf_failed`` problem for the API, Django's page elsewhere.

    Args:
        request: The rejected request.
        reason: Django's failure reason (not exposed to API clients).
    """
    if is_api(request):
        return _problem(403, "csrf_failed", CSRF_DETAIL)
    return django_csrf_failure(request, reason)


def not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """``handler404``: ``not_found`` problem for the API, the normal page elsewhere.

    Args:
        request: The request.
        exception: The Http404 raised.
    """
    if is_api(request):
        return _problem(404, "not_found", "Not found.")
    return defaults.page_not_found(request, exception)


def api_not_found(request: HttpRequest, path: str = "") -> HttpResponse:
    """Catch-all for unknown ``/api/v1/`` paths: a ``not_found`` problem even with DEBUG on.

    Args:
        request: The request.
        path: The unmatched rest of the path.
    """
    return _problem(404, "not_found", "Not found.")


def server_error(request: HttpRequest) -> HttpResponse:
    """``handler500``: ``internal_error`` problem for the API, the normal page elsewhere.

    Args:
        request: The request.
    """
    if is_api(request):
        return _problem(500, "internal_error", "Internal server error.")
    return defaults.server_error(request)
