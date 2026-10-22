import logging
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.http import HttpRequest, HttpResponseBase
from django.utils.decorators import sync_and_async_middleware

REQUEST_ID_HEADER = "X-Request-ID"
MAX_REQUEST_ID_LENGTH = 64

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

type SyncHandler = Callable[[HttpRequest], HttpResponseBase]
type AsyncHandler = Callable[[HttpRequest], Awaitable[HttpResponseBase]]


class RequestIdFilter(logging.Filter):
    """Adds the current request id to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Attach ``request_id`` and keep the record.

        Args:
            record: The log record being emitted.

        Returns:
            Always True.
        """
        record.request_id = request_id_var.get()
        return True


def _bind_request_id(request: HttpRequest) -> str:
    """Take the incoming request id (or make one) and bind it to the context.

    Args:
        request: The current request.

    Returns:
        The request id now bound to this context.
    """
    incoming = request.headers.get(REQUEST_ID_HEADER, "")
    request_id = incoming[:MAX_REQUEST_ID_LENGTH] if incoming.isprintable() and incoming else ""
    request_id = request_id or uuid.uuid4().hex
    request_id_var.set(request_id)
    return request_id


@sync_and_async_middleware
def request_id_middleware(get_response: SyncHandler | AsyncHandler) -> SyncHandler | AsyncHandler:
    """Bind a request id for logs and echo it in the response header.

    Works for both sync and async views, so the SSE stream keeps async.

    Args:
        get_response: The next handler in the chain.

    Returns:
        A sync or async middleware matching ``get_response``.
    """
    if iscoroutinefunction(get_response):
        async_next: AsyncHandler = get_response

        async def async_middleware(request: HttpRequest) -> HttpResponseBase:
            """Async branch of the middleware."""
            request_id = _bind_request_id(request)
            response = await async_next(request)
            response[REQUEST_ID_HEADER] = request_id
            return response

        return markcoroutinefunction(async_middleware)

    sync_next: SyncHandler = get_response  # type: ignore[assignment]

    def sync_middleware(request: HttpRequest) -> HttpResponseBase:
        """Sync branch of the middleware."""
        request_id = _bind_request_id(request)
        response = sync_next(request)
        response[REQUEST_ID_HEADER] = request_id
        return response

    return sync_middleware
