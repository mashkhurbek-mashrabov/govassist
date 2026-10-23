"""The streaming chat endpoint: an async Django view (DRF has no async views)."""

from django.conf import settings
from django.http import HttpRequest, HttpResponseBase, StreamingHttpResponse
from pydantic import ValidationError

from apps.accounts.models import User
from apps.accounts.selectors import ais_email_verified
from apps.chat.constants import SSE_HEADERS
from apps.chat.generator import GeminiAnswerGenerator
from apps.chat.limits import QuotaService
from apps.chat.schemas import ChatRequest
from apps.chat.service import AnswerService
from apps.chat.sse import sse_stream
from apps.common.gemini import aclose_client, get_client
from apps.common.problems import (
    EmailNotVerified,
    InvalidInput,
    MethodNotAllowedProblem,
    NotSignedIn,
    Problem,
    ProfileIncomplete,
    problem_response,
)
from apps.corpus.embeddings import GeminiEmbedder


def build_answer_service() -> AnswerService:
    """Wire the production collaborators (Gemini embedder and generator, Redis quotas).

    Embedder and generator share one Gemini client, closed by the service when the stream
    ends (or by the view when the request fails before streaming).
    """
    client = get_client()
    return AnswerService(
        embedder=GeminiEmbedder(
            client, max_tries=settings.CHAT_EMBED_MAX_TRIES, honor_server_delay=False
        ),
        generator_factory=lambda: GeminiAnswerGenerator(client),
        quota=QuotaService(),
        on_close=lambda: aclose_client(client),
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


async def chat_stream(request: HttpRequest) -> HttpResponseBase:
    """``POST /api/v1/chat``: stream an answer as SSE (contract §4).

    Errors found before the stream starts are problem+json; later ones are ``error`` events.
    CSRF is enforced by ``CsrfViewMiddleware``.

    Args:
        request: The incoming request.
    """
    if request.method != "POST":
        not_allowed = problem_response(MethodNotAllowedProblem())
        not_allowed["Allow"] = "POST"
        return not_allowed
    try:
        user = await _signed_in_user(request)
        body = _parse(request.body)
    except Problem as problem:
        return problem_response(problem)
    service = build_answer_service()
    try:
        conversation = await service.prepare(user, body.conversation_id)
    except Problem as problem:
        await service.aclose()
        return problem_response(problem)
    events = service.answer(user, conversation, body.text)
    return StreamingHttpResponse(
        sse_stream(events, interval=settings.SSE_KEEPALIVE_S),
        content_type="text/event-stream",
        headers=SSE_HEADERS,
    )
