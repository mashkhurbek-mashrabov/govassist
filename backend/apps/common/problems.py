"""RFC 9457 problem+json errors, shared by DRF views and the async SSE view."""

import logging
from http import HTTPStatus
from typing import Any, Literal

from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from rest_framework import exceptions, status
from rest_framework.response import Response

from apps.common.constants import PROBLEM_CONTENT_TYPE

logger = logging.getLogger(__name__)


class Problem(exceptions.APIException):
    """An API error with a contract `code` (docs/contract.md §1).

    Subclasses set ``status_code``, ``default_code`` and ``default_detail``.
    """

    status_code: int = status.HTTP_400_BAD_REQUEST
    default_code = "validation_error"
    default_detail = "Bad request."

    def __init__(
        self,
        detail: str | None = None,
        *,
        retry_after: int | None = None,
        errors: dict[str, list[str]] | None = None,
    ) -> None:
        super().__init__(detail=detail)
        self.retry_after = retry_after
        self.errors = errors

    def extensions(self) -> dict[str, Any]:
        """Extra problem members for this error (none by default)."""
        return {}


class InvalidInput(Problem):
    """Request body failed validation; ``errors`` lists messages per field."""

    default_detail = "Invalid input."


class NotSignedIn(Problem):
    """No session (for views outside DRF)."""

    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "not_authenticated"
    default_detail = "Authentication credentials were not provided."


class ResourceNotFound(Problem):
    """Resource missing or not the user's own (for views outside DRF)."""

    status_code = status.HTTP_404_NOT_FOUND
    default_code = "not_found"
    default_detail = "Not found."


class CsrfFailed(Problem):
    """The CSRF token is missing or wrong."""

    status_code = status.HTTP_403_FORBIDDEN
    default_code = "csrf_failed"
    default_detail = "CSRF check failed. Reload the page and try again."


class MethodNotAllowedProblem(Problem):
    """HTTP method not supported by the endpoint (for views outside DRF)."""

    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_code = "method_not_allowed"
    default_detail = "Method not allowed."


class EmailNotVerified(Problem):
    """The user has not verified the email address yet."""

    status_code = status.HTTP_403_FORBIDDEN
    default_code = "email_not_verified"
    default_detail = "Verify your email address first."


class ProfileIncomplete(Problem):
    """Region or district is missing; the user must finish onboarding."""

    status_code = status.HTTP_403_FORBIDDEN
    default_code = "profile_incomplete"
    default_detail = "Choose your region and district first."


class StreamInProgress(Problem):
    """The user already has an answer streaming."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "stream_in_progress"
    default_detail = "An answer is already being written."


class RateLimited(Problem):
    """A per-user hourly limit was hit."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_code = "rate_limited"
    default_detail = "Too many questions. Try again later."


class QuotaExceeded(Problem):
    """A daily per-user limit or the global token cap was hit."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_code = "quota_exceeded"
    default_detail = "Daily limit reached. Try again tomorrow."

    def __init__(
        self,
        detail: str | None = None,
        *,
        retry_after: int | None = None,
        scope: Literal["user", "global"] = "user",
    ) -> None:
        super().__init__(detail, retry_after=retry_after)
        self.scope = scope

    def extensions(self) -> dict[str, Any]:
        """``scope``: the user's daily limit or the service-wide token cap."""
        return {"scope": self.scope}


class LLMUnavailable(Problem):
    """Gemini failed before streaming started."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "llm_unavailable"
    default_detail = "The answer service is unavailable. Try again later."


def problem_body(
    status_code: int,
    code: str,
    detail: str,
    *,
    errors: dict[str, Any] | None = None,
    retry_after: int | None = None,
    extensions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a problem+json body in the contract's shape.

    Args:
        status_code: HTTP status.
        code: Contract error code, e.g. ``rate_limited``.
        detail: Human-readable explanation.
        errors: Field errors for ``validation_error``.
        retry_after: Seconds until the client may retry.
        extensions: Extra members such as ``scope``.

    Returns:
        The JSON-serializable body.
    """
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": HTTPStatus(status_code).phrase,
        "status": status_code,
        "detail": detail,
        "code": code,
        "errors": errors,
    }
    if retry_after is not None:
        body["retry_after"] = retry_after
    return body | (extensions or {})


def _retry_headers(retry_after: int | None) -> dict[str, str]:
    """Return the ``Retry-After`` header when a wait is known."""
    return {} if retry_after is None else {"Retry-After": str(retry_after)}


def problem_response(problem: Problem) -> JsonResponse:
    """Render a ``Problem`` as a plain Django response (for non-DRF views).

    Args:
        problem: The raised problem.

    Returns:
        A problem+json response with any ``Retry-After`` header.
    """
    body = problem_body(
        problem.status_code,
        str(problem.default_code),
        str(problem.detail),
        errors=problem.errors,
        retry_after=problem.retry_after,
        extensions=problem.extensions(),
    )
    return JsonResponse(
        body,
        status=problem.status_code,
        content_type=PROBLEM_CONTENT_TYPE,
        headers=_retry_headers(problem.retry_after),
    )


def _classify(exc: Exception) -> tuple[int, str, str, dict[str, Any] | None, int | None]:  # noqa: PLR0911
    """Map an exception to (status, code, detail, errors, retry_after).

    Args:
        exc: Any exception raised inside a DRF view.

    Returns:
        The problem fields for the exception.
    """
    match exc:
        case Problem():
            code = str(exc.default_code)
            return exc.status_code, code, str(exc.detail), exc.errors, exc.retry_after
        case exceptions.NotAuthenticated() | exceptions.AuthenticationFailed():
            return 401, "not_authenticated", str(exc.detail), None, None
        case exceptions.ValidationError():
            detail = (
                exc.detail if isinstance(exc.detail, dict) else {"non_field_errors": exc.detail}
            )
            return 400, "validation_error", "Invalid input.", dict(detail), None
        case exceptions.Throttled():
            seconds = getattr(exc, "wait", None)
            wait = int(seconds) if seconds is not None else None
            return 429, "rate_limited", "Too many requests.", None, wait
        case exceptions.NotFound() | Http404():
            return 404, "not_found", "Not found.", None, None
        case exceptions.PermissionDenied():
            return 403, "permission_denied", str(exc.detail), None, None
        case PermissionDenied():
            return 403, "permission_denied", "You do not have permission.", None, None
        case exceptions.APIException():
            return exc.status_code, str(exc.default_code), str(exc.detail), None, None
        case _:
            logger.exception("Unhandled API error")
            return 500, "internal_error", "Internal server error.", None, None


def exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    """DRF exception handler that emits problem+json for every error.

    Args:
        exc: The raised exception.
        context: DRF handler context (unused).

    Returns:
        A problem+json response.
    """
    status_code, code, detail, errors, retry_after = _classify(exc)
    extensions = exc.extensions() if isinstance(exc, Problem) else None
    body = problem_body(
        status_code, code, detail, errors=errors, retry_after=retry_after, extensions=extensions
    )
    return Response(
        body,
        status=status_code,
        content_type=PROBLEM_CONTENT_TYPE,
        headers=_retry_headers(retry_after),
    )
