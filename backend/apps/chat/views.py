"""The streaming chat endpoint: an async Django view (DRF has no async views)."""

from django.conf import settings
from django.http import HttpRequest, HttpResponseBase, StreamingHttpResponse
from django.views.decorators.http import require_POST
from pydantic import ValidationError

from apps.accounts.models import User
from apps.accounts.selectors import ais_email_verified
from apps.chat.generator import GeminiAnswerGenerator
from apps.chat.limits import QuotaService
from apps.chat.schemas import ChatRequest
from apps.chat.service import AnswerService
from apps.chat.sse import sse_stream
from apps.common.problems import (
    EmailNotVerified,
    InvalidInput,
    NotSignedIn,
    Problem,
    ProfileIncomplete,
    problem_response,
)
from apps.corpus.embeddings import GeminiEmbedder

SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


def build_answer_service() -> AnswerService:
    """Wire the production collaborators (Gemini embedder and generator, Redis quotas)."""
    return AnswerService(
        embedder=GeminiEmbedder(), generator_factory=GeminiAnswerGenerator, quota=QuotaService()
    )


def _parse(body: bytes) -> ChatRequest:
    """Validate the request body.

    Raises:
        InvalidInput: On bad JSON, unknown fields or a too long question.
    """
    try:
        request = ChatRequest.model_validate_json(body)
    except ValidationError as exc:
        errors: dict[str, list[str]] = {}
        for error in exc.errors():
            field = ".".join(str(part) for part in error["loc"]) or "non_field_errors"
            errors.setdefault(field, []).append(error["msg"])
        raise InvalidInput(errors=errors) from exc
    if len(request.text) > settings.QUESTION_MAX_CHARS:
        message = f"At most {settings.QUESTION_MAX_CHARS} characters."
        raise InvalidInput(errors={"text": [message]})
    return request


async def _signed_in_user(request: HttpRequest) -> User:
    """Return the user allowed to ask questions.

    Raises:
        NotSignedIn | EmailNotVerified | ProfileIncomplete: When not allowed.
    """
    user = await request.auser()
    if not isinstance(user, User):
        raise NotSignedIn
    if not await ais_email_verified(user):
        raise EmailNotVerified
    if not user.profile_complete:
        raise ProfileIncomplete
    return user


@require_POST
async def chat_stream(request: HttpRequest) -> HttpResponseBase:
    """``POST /api/v1/chat``: stream an answer as SSE (contract §4).

    Errors found before the stream starts are problem+json; later ones are ``error`` events.
    CSRF is enforced by ``CsrfViewMiddleware``.

    Args:
        request: The incoming request.
    """
    try:
        user = await _signed_in_user(request)
        body = _parse(request.body)
        service = build_answer_service()
        conversation = await service.prepare(user, body.conversation_id)
    except Problem as problem:
        return problem_response(problem)
    events = service.answer(user, conversation, body.text)
    return StreamingHttpResponse(
        sse_stream(events, interval=settings.SSE_KEEPALIVE_S),
        content_type="text/event-stream",
        headers=SSE_HEADERS,
    )
