"""API tests for POST /api/v1/chat (SSE), with FakeEmbedder and fake generators."""

import asyncio
import json
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any

import pytest
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.db import connections
from django.test import AsyncClient, override_settings

from apps.accounts.models import User
from apps.chat.generator import AnswerGenerator, FakeAnswerGenerator, Usage
from apps.chat.limits import QuotaService
from apps.chat.models import Conversation, Message, Retrieval
from apps.chat.prompts import Prompt
from apps.chat.service import AnswerService
from apps.corpus.embeddings import FakeEmbedder
from apps.corpus.models import Document
from apps.geo.models import District
from apps.offices.models import OfficeType
from conftest import answer_json, make_office, make_user

pytestmark = pytest.mark.django_db(transaction=True)
QUESTION = "Pasportni almashtirish uchun nima qilish kerak? Tel: +998 90 123 45 67"


class _Recorder:
    """Builds the service with a chosen generator and remembers the generators made."""

    def __init__(self) -> None:
        self.factory: Callable[[], AnswerGenerator] = lambda: FakeAnswerGenerator(answer_json())
        self.embedder: Any = FakeEmbedder()
        self.made: list[AnswerGenerator] = []

    def build(self) -> AnswerService:
        """Return a service wired with fakes."""

        def factory() -> AnswerGenerator:
            """Create and remember one generator."""
            generator = self.factory()
            self.made.append(generator)
            return generator

        return AnswerService(
            embedder=self.embedder, generator_factory=factory, quota=QuotaService()
        )


@pytest.fixture(autouse=True)
async def _close_thread_connections() -> AsyncIterator[None]:
    """Close the DB connection sync_to_async opened in its worker thread."""
    yield
    await sync_to_async(connections.close_all)()


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> Iterator[_Recorder]:
    """Patch the view's service builder."""
    recorder = _Recorder()
    monkeypatch.setattr("apps.chat.views.build_answer_service", recorder.build)
    yield recorder


@pytest.fixture
async def client(user: User) -> AsyncClient:
    """An async client logged in as the verified user with a complete profile."""
    client = AsyncClient()
    await client.aforce_login(user)
    return client


def _parse(raw: str) -> list[tuple[str, dict[str, Any]]]:
    """Split an SSE body into (event, data) pairs, ignoring comments."""
    events = []
    for block in raw.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines() if not line.startswith(":"))
        if lines:
            events.append((lines["event"], json.loads(lines["data"])))
    return events


async def _ask(client: AsyncClient, **body: Any) -> list[tuple[str, dict[str, Any]]]:
    """POST a question and read the whole stream."""
    response: Any = await client.post("/api/v1/chat", {"text": QUESTION} | body, "application/json")
    assert response.streaming, response.content
    assert response["Content-Type"] == "text/event-stream"
    assert response["Cache-Control"] == "no-cache"
    assert response["X-Accel-Buffering"] == "no"
    chunks = [chunk async for chunk in response.streaming_content]
    return _parse(b"".join(chunks).decode())


async def test_happy_path_event_order_and_persistence(
    client: AsyncClient,
    recorder: _Recorder,
    user: User,
    passport_doc: Document,
    office_type: OfficeType,
    district: District,
) -> None:
    """Meta → status → office → delta* → final → done, and everything is stored."""
    await sync_to_async(make_office)(office_type, district)
    events = await _ask(client)
    names = [name for name, _ in events]
    assert names[:5] == ["meta", "status", "status", "office", "status"]
    assert [data["stage"] for name, data in events if name == "status"] == [
        "searching",
        "found",
        "writing",
    ]
    assert set(names[5:-2]) == {"delta"}
    assert names[-2:] == ["final", "done"]
    assert "".join(d["text"] for n, d in events if n == "delta") == answer_json()

    meta, office = events[0][1], events[3][1]
    assert office["match"] == "district"
    message = events[-2][1]["message"]
    assert message["id"] == meta["assistant_message_id"]
    assert message["status"] == "complete"
    assert message["error_code"] is None
    assert message["answer"]["steps"][0]["source_ids"] == ["S1"]
    assert [s["id"] for s in message["sources"]] == ["S1"]
    assert message["sources"][0] == {
        "id": "S1",
        "kind": "service_page",
        "title": "NAMUNA passport",
        "publisher": "example.org",
        "url": "https://example.org/passport",
        "section": "2-modda",
        "published_at": None,
        "fetched_at": message["sources"][0]["fetched_at"],
    }
    assert message["sources"][0]["fetched_at"].endswith("Z")
    assert message["office"] == office
    assert message["refused"] is False
    assert message["feedback"] is None

    question = await Message.objects.aget(id=meta["user_message_id"])
    assert "[PHONE]" in question.text
    assert "998" not in question.text
    prompt = recorder.made[0].prompts[0]  # type: ignore[attr-defined]
    assert "[PHONE]" in prompt.user
    assert "998 90" not in prompt.user
    assistant = await Message.objects.aget(id=meta["assistant_message_id"])
    assert (assistant.model, assistant.prompt_version) == ("fake-generator", "v1")
    assert (assistant.prompt_tokens, assistant.completion_tokens) == (100, 50)
    assert assistant.latency_ms is not None
    assert assistant.retrieval_ms is not None
    cited = [r.cited async for r in Retrieval.objects.filter(message=assistant).order_by("rank")]
    assert cited == [True]
    conversation = await Conversation.objects.aget(id=meta["conversation_id"])
    assert conversation.title == "NAMUNA pasport"
    usage = await QuotaService().ausage(user.id)
    assert usage.day_used == 1
    assert await QuotaService().atokens_today() == 150


async def test_follow_up_uses_history_and_same_conversation(
    client: AsyncClient, recorder: _Recorder, passport_doc: Document
) -> None:
    """A second question continues the conversation and sends the earlier turn as history."""
    first = await _ask(client)
    conversation_id = first[0][1]["conversation_id"]
    second = await _ask(client, conversation_id=conversation_id, text="Yana bir savol")
    assert second[0][1]["conversation_id"] == conversation_id
    history = recorder.made[1].prompts[0].user  # type: ignore[attr-defined]
    assert "Assistant: NAMUNA pasport — NAMUNA xulosa." in history


async def test_refused_answer(
    client: AsyncClient, recorder: _Recorder, passport_doc: Document
) -> None:
    """not_found answers are stored as refused, with no sources."""
    recorder.factory = lambda: FakeAnswerGenerator(answer_json(answer_type="not_found"))
    message = (await _ask(client))[-2][1]["message"]
    assert message["refused"] is True
    assert message["sources"] == []
    assert message["answer"]["steps"] == []


class _Failing:
    """A generator that fails in a chosen way."""

    model_name = "failing"

    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.usage = Usage(prompt_tokens=7)

    async def stream(self, prompt: Prompt) -> AsyncIterator[str]:
        """Fail, hang or emit broken JSON."""
        if self.mode == "hang":
            await asyncio.sleep(3600)
        if self.mode == "crash":
            raise ConnectionError("gemini down")
        yield '{"answer_type": "service"'


@pytest.mark.parametrize(
    ("mode", "code"),
    [("broken", "invalid_answer"), ("crash", "llm_unavailable"), ("hang", "llm_timeout")],
)
@override_settings(LLM_TIMEOUT_S=0)
async def test_generation_failures_become_error_events(
    client: AsyncClient, recorder: _Recorder, passport_doc: Document, mode: str, code: str
) -> None:
    """Every generation failure ends with one error event and a failed message."""
    recorder.factory = lambda: _Failing(mode)
    if mode != "hang":
        override = override_settings(LLM_TIMEOUT_S=40)
        override.enable()
    try:
        events = await _ask(client)
    finally:
        if mode != "hang":
            override.disable()
    assert events[-1] == ("error", events[-1][1])
    assert events[-1][1]["code"] == code
    assistant = await Message.objects.aget(id=events[0][1]["assistant_message_id"])
    assert (assistant.status, assistant.error_code, assistant.answer) == ("failed", code, None)
    assert assistant.prompt_tokens == 7


async def test_embedding_failure(client: AsyncClient, recorder: _Recorder) -> None:
    """A failing query embedding is llm_unavailable."""

    class Broken(FakeEmbedder):
        """Embedder that cannot reach Gemini."""

        async def embed_query(self, query: str) -> list[float]:
            """Fail like a network error."""
            raise ConnectionError("down")

    recorder.embedder = Broken()
    events = await _ask(client)
    assert [n for n, _ in events] == ["meta", "status", "error"]
    assert events[-1][1]["code"] == "llm_unavailable"


async def test_unexpected_error_is_internal(
    client: AsyncClient, recorder: _Recorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Bugs become internal_error events, never a broken stream."""

    def explode(*args: Any, **kwargs: Any) -> list[Any]:
        """A crashing search."""
        raise RuntimeError("bug")

    monkeypatch.setattr("apps.chat.service.search", explode)
    service = recorder.build()
    service._search = explode
    monkeypatch.setattr("apps.chat.views.build_answer_service", lambda: service)
    events = await _ask(client)
    assert events[-1][1]["code"] == "internal_error"


async def test_client_stop_marks_message_stopped(
    client: AsyncClient, recorder: _Recorder, user: User, passport_doc: Document
) -> None:
    """A disconnect mid-answer stores failed/stopped with no answer and frees the lock."""
    recorder.factory = lambda: _Failing("hang")
    response: Any = await client.post("/api/v1/chat", {"text": QUESTION}, "application/json")
    stream = response.streaming_content
    first = (await anext(stream)).decode()
    assistant_id = json.loads(first.split("data: ", 1)[1])["assistant_message_id"]
    while b'"writing"' not in await anext(stream):
        pass
    reader = asyncio.ensure_future(anext(stream))
    await asyncio.sleep(0.2)
    reader.cancel()
    with pytest.raises(asyncio.CancelledError):
        await reader
    await asyncio.sleep(0.1)
    assistant = await Message.objects.aget(id=assistant_id)
    assert (assistant.status, assistant.error_code, assistant.answer) == ("failed", "stopped", None)
    assert await cache.aget(f"stream:{user.id}") is None


async def _post(client: AsyncClient, body: Any = None) -> Any:
    """POST /chat and return the (non-streaming) problem response."""
    return await client.post("/api/v1/chat", body or {"text": "Savol?"}, "application/json")


async def test_anonymous_is_401(recorder: _Recorder) -> None:
    """No session: not_authenticated."""
    response = await _post(AsyncClient())
    assert response.status_code == 401
    assert response["Content-Type"] == "application/problem+json"
    assert response.json()["code"] == "not_authenticated"


async def test_unverified_and_incomplete_are_403(recorder: _Recorder, district: District) -> None:
    """Unverified email, then missing district, each block the chat."""
    client = AsyncClient()
    await client.aforce_login(await sync_to_async(make_user)("u@example.com", verified=False))
    assert (await _post(client)).json()["code"] == "email_not_verified"
    await client.aforce_login(await sync_to_async(make_user)("v@example.com"))
    assert (await _post(client)).json()["code"] == "profile_incomplete"


@pytest.mark.parametrize(
    "body",
    [{"text": ""}, {"text": "x" * 1001}, {"conversation_id": "nope", "text": "a"}, {"x": 1}],
)
async def test_bad_bodies_are_400(client: AsyncClient, recorder: _Recorder, body: Any) -> None:
    """Invalid bodies are validation errors with field messages."""
    response = await _post(client, body)
    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
    assert response.json()["errors"]


async def test_unknown_conversation_is_404(client: AsyncClient, recorder: _Recorder) -> None:
    """Someone else's or a missing conversation: not_found."""
    body = {"text": "a", "conversation_id": "01a16308-906a-724b-9123-ad990bfb808b"}
    assert (await _post(client, body)).json()["code"] == "not_found"


async def test_second_stream_is_409(client: AsyncClient, recorder: _Recorder, user: User) -> None:
    """One stream per user."""
    await cache.aset(f"stream:{user.id}", 1, 60)
    response = await _post(client)
    assert response.status_code == 409
    assert response.json()["code"] == "stream_in_progress"


@override_settings(CHAT_LIMIT_HOUR=0)
async def test_hourly_limit_is_429(client: AsyncClient, recorder: _Recorder) -> None:
    """rate_limited with Retry-After."""
    response = await _post(client)
    assert response.status_code == 429
    assert response.json()["code"] == "rate_limited"
    assert int(response["Retry-After"]) > 0


@override_settings(GLOBAL_DAILY_TOKEN_CAP=0)
async def test_global_cap_is_429_with_scope(client: AsyncClient, recorder: _Recorder) -> None:
    """quota_exceeded carries scope=global."""
    body = (await _post(client)).json()
    assert (body["code"], body["scope"]) == ("quota_exceeded", "global")


async def test_get_is_not_allowed(client: AsyncClient) -> None:
    """Only POST."""
    assert (await client.get("/api/v1/chat")).status_code == 405


async def test_csrf_is_enforced(user: User, recorder: _Recorder) -> None:
    """Without the CSRF token the browser session cannot post."""
    client = AsyncClient(enforce_csrf_checks=True)
    await client.aforce_login(user)
    assert (await _post(client)).status_code == 403


async def test_client_drop_before_iteration_leaves_no_lock(
    client: AsyncClient, recorder: _Recorder, user: User
) -> None:
    """The lock is taken inside the stream: a response never iterated holds nothing."""
    response: Any = await client.post("/api/v1/chat", {"text": QUESTION}, "application/json")
    assert response.streaming
    del response
    assert await cache.aget(f"stream:{user.id}") is None


async def test_lost_lock_race_is_one_error_event(
    client: AsyncClient, recorder: _Recorder, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Another stream grabbing the lock after the pre-check ends this one, keeping its lock."""
    response: Any = await client.post("/api/v1/chat", {"text": QUESTION}, "application/json")
    await cache.aset(f"stream:{user.id}", "other", 60)
    chunks = [chunk async for chunk in response.streaming_content]
    events = _parse(b"".join(chunks).decode())
    assert [name for name, _ in events] == ["error"]
    assert events[0][1]["code"] == "stream_in_progress"
    assert await cache.aget(f"stream:{user.id}") == "other"
    assert not await Conversation.objects.aexists()


def test_lock_ttl_default_follows_llm_timeout() -> None:
    """The lock outlives the longest answer: LLM_TIMEOUT_S + 30 s by default."""
    from config.settings import base  # noqa: PLC0415

    assert base.STREAM_LOCK_TTL_S == base.LLM_TIMEOUT_S + 30


async def test_title_from_question_then_first_answer(
    client: AsyncClient, recorder: _Recorder, passport_doc: Document
) -> None:
    """A failed first question titles the conversation; the first answer replaces it once."""
    recorder.factory = lambda: _Failing("broken")
    long_question = "Pasport " + "uzun savol " * 10 + "+998 90 123 45 67"
    first = await _ask(client, text=long_question)
    conversation_id = first[0][1]["conversation_id"]
    conversation = await Conversation.objects.aget(id=conversation_id)
    assert conversation.title == long_question[:60].strip()
    assert len(conversation.title) <= 60

    recorder.factory = lambda: FakeAnswerGenerator(answer_json())
    await _ask(client, conversation_id=conversation_id)
    await conversation.arefresh_from_db()
    assert conversation.title == "NAMUNA pasport"

    recorder.factory = lambda: FakeAnswerGenerator(answer_json(title="NAMUNA boshqa"))
    await _ask(client, conversation_id=conversation_id)
    await conversation.arefresh_from_db()
    assert conversation.title == "NAMUNA pasport"


async def test_title_is_scrubbed(client: AsyncClient, recorder: _Recorder) -> None:
    """The question-based title never contains PII."""
    recorder.factory = lambda: _Failing("crash")
    events = await _ask(client, text="AA1234567 pasportim yoʻqoldi")
    conversation = await Conversation.objects.aget(id=events[0][1]["conversation_id"])
    assert conversation.title.startswith("[PASSPORT]")
