"""Answer orchestration for ``POST /api/v1/chat`` (plan §3 answer flow, §11, contract §4)."""

import asyncio
import logging
import time
from collections.abc import AsyncGenerator, Callable, Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Any
from uuid import UUID

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from pydantic import ValidationError

from apps.accounts.models import User
from apps.chat.api.serializers import serialize_message
from apps.chat.citations import Citations, resolve_citations
from apps.chat.generator import AnswerGenerator
from apps.chat.limits import QuotaService
from apps.chat.models import Conversation, Message, Retrieval
from apps.chat.prompts import ContextBlock, Prompt, Turn, render_prompt
from apps.chat.schemas import Answer
from apps.chat.sse import Event
from apps.common.i18n import Lang
from apps.common.pii import scrub
from apps.common.problems import ResourceNotFound, StreamInProgress
from apps.common.text import detect_language
from apps.common.time import isoformat_utc
from apps.corpus.embeddings import Embedder
from apps.corpus.models import Chunk
from apps.offices.locator import locate
from apps.retrieval.search import Hit, search

logger = logging.getLogger(__name__)

MS_PER_S = 1000
STOPPED = "stopped"
TITLE_FROM_QUESTION_CHARS = 60
HEADING_SEPARATOR = " › "

type Locator = Callable[..., dict[str, Any] | None]
type Searcher = Callable[..., list[Hit]]


class AnswerError(Exception):
    """A failure that ends the stream with an ``error`` event."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class _Run:
    """Mutable state of one answer run, shared with the failure handlers."""

    started: float
    retrieval_ms: int | None = None
    assistant: Message | None = None
    generator: AnswerGenerator | None = None


@dataclass(frozen=True)
class _Context:
    """Retrieved chunks as prompt blocks plus their contract ``Source`` dicts."""

    hits: list[Hit]
    blocks: list[ContextBlock]
    sources: dict[str, dict[str, Any]]


def _label(rank: int) -> str:
    """Context label for a 1-based rank: ``S1``, ``S2`` and so on."""
    return f"S{rank}"


def _section(chunk: Chunk) -> str | None:
    """The most specific heading of a chunk, else the document's section label."""
    if chunk.heading_path:
        return chunk.heading_path.split(HEADING_SEPARATOR)[-1]
    return chunk.document.section_label


def _source(label: str, chunk: Chunk) -> dict[str, Any]:
    """Build the contract ``Source`` for a chunk's document.

    Args:
        label: The context label.
        chunk: A chunk with its document loaded.
    """
    document = chunk.document
    return {
        "id": label,
        "kind": document.kind,
        "title": document.title,
        "publisher": document.publisher,
        "url": document.url,
        "section": _section(chunk),
        "published_at": document.published_at.isoformat() if document.published_at else None,
        "fetched_at": isoformat_utc(document.fetched_at),
    }


def build_context(hits: Sequence[Hit]) -> _Context:
    """Load the hit chunks and label them S1..Sn in rank order.

    Args:
        hits: Retrieval hits, best first.
    """
    chunks = Chunk.objects.select_related("document").in_bulk([hit.chunk_id for hit in hits])
    present = [hit for hit in hits if hit.chunk_id in chunks]
    blocks, sources = [], {}
    for position, hit in enumerate(present, start=1):
        chunk, label = chunks[hit.chunk_id], _label(position)
        source = _source(label, chunk)
        sources[label] = source
        blocks.append(
            ContextBlock(
                label=label,
                title=source["title"],
                publisher=source["publisher"],
                section=source["section"],
                published_at=source["published_at"],
                text=chunk.text,
            )
        )
    return _Context(hits=present, blocks=blocks, sources=sources)


def recent_turns(conversation: Conversation, before: Message) -> list[Turn]:
    """The last ``HISTORY_TURNS`` completed exchanges before ``before``, oldest first.

    Args:
        conversation: The conversation.
        before: The current user message (excluded).
    """
    messages = list(
        conversation.messages.filter(created_at__lt=before.created_at).order_by("-created_at")[
            : settings.HISTORY_TURNS * 2
        ]
    )[::-1]
    turns: list[Turn] = []
    for question, reply in pairwise(messages):
        answer = reply.answer if reply.role == Message.Role.ASSISTANT else None
        if question.role == Message.Role.USER and answer:
            turns.append(Turn(question.text, answer["title"], answer["summary"]))
    return turns[-settings.HISTORY_TURNS :]


@transaction.atomic
def save_answer(
    assistant: Message,
    citations: Citations,
    context: _Context,
    office: dict[str, Any] | None,
    run: dict[str, Any],
) -> Message:
    """Persist a completed answer, its retrieval rows and the conversation title.

    Args:
        assistant: The streaming assistant message.
        citations: Resolved answer and cited sources.
        context: The retrieval set shown to the model.
        office: The ``OfficeMatch`` sent to the client, if any.
        run: Model/prompt/corpus versions, token counts and timings.

    Returns:
        The saved message.
    """
    answer = citations.answer
    assistant.answer = answer.model_dump(mode="json")
    assistant.sources = citations.sources
    assistant.office_match = office
    assistant.refused = answer.refused
    assistant.status = Message.Status.COMPLETE
    assistant.language = answer.language
    for name, value in run.items():
        setattr(assistant, name, value)
    assistant.save()
    Retrieval.objects.bulk_create(
        Retrieval(
            message=assistant,
            chunk_id=hit.chunk_id,
            label=_label(position),
            rank=hit.rank,
            vector_score=hit.vector_score,
            keyword_score=hit.keyword_score,
            fused_score=hit.fused_score,
            cited=_label(position) in citations.cited_labels,
        )
        for position, hit in enumerate(context.hits, start=1)
    )
    conversation = assistant.conversation
    earlier_answers = conversation.messages.filter(
        role=Message.Role.ASSISTANT, status=Message.Status.COMPLETE
    ).exclude(id=assistant.id)
    if not earlier_answers.exists():
        conversation.title = answer.title
    conversation.save(update_fields=["title", "updated_at"])
    return assistant


class AnswerService:
    """Turns one question into the SSE event sequence; every collaborator is injected."""

    def __init__(
        self,
        *,
        embedder: Embedder,
        generator_factory: Callable[[], AnswerGenerator],
        quota: QuotaService,
        searcher: Searcher = search,
        locator: Locator = locate,
    ) -> None:
        self._embedder = embedder
        self._generator_factory = generator_factory
        self._quota = quota
        self._search = searcher
        self._locate = locator

    async def prepare(self, user: User, conversation_id: UUID | None) -> Conversation | None:
        """Pre-stream checks that answer with problem+json: ownership, quotas, busy stream.

        Nothing is acquired here: the stream lock is taken inside :meth:`answer`, so a client
        that drops before the stream starts leaves no lock behind.

        Args:
            user: The signed-in, verified user with a complete profile.
            conversation_id: The conversation to continue, or None for a new one.

        Returns:
            The existing conversation, or None.

        Raises:
            ResourceNotFound: The conversation is not the user's.
            QuotaExceeded | RateLimited: A limit is reached.
            StreamInProgress: Another answer is streaming.
        """
        conversation = None
        if conversation_id is not None:
            conversation = await Conversation.objects.filter(user=user, id=conversation_id).afirst()
            if conversation is None:
                raise ResourceNotFound
        await self._quota.acheck(user.id)
        if await self._quota.astream_active(user.id):
            raise StreamInProgress
        return conversation

    async def _open_turn(
        self, user: User, conversation: Conversation | None, text: str, lang: Lang
    ) -> tuple[Conversation, Message, Message]:
        """Create the conversation (if new), the user message and the streaming answer."""
        if conversation is None:
            title = text[:TITLE_FROM_QUESTION_CHARS].strip()
            conversation = await Conversation.objects.acreate(user=user, language=lang, title=title)
        question = await Message.objects.acreate(
            conversation=conversation, role=Message.Role.USER, text=text, language=lang
        )
        assistant = await Message.objects.acreate(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            status=Message.Status.STREAMING,
            language=lang,
        )
        return conversation, question, assistant

    async def _retrieve(self, question: str, lang: Lang) -> list[Hit]:
        """Embed the question and run hybrid search.

        Raises:
            AnswerError: ``llm_unavailable`` when the query embedding fails.
        """
        try:
            vector = await self._embedder.embed_query(question)
        except Exception as exc:
            logger.warning("Query embedding failed", exc_info=True)
            raise AnswerError("llm_unavailable", "The answer service is unavailable.") from exc
        return await sync_to_async(self._search)(question, lang, query_vector=vector)

    async def _generate(
        self, generator: AnswerGenerator, prompt: Prompt, fragments: list[str]
    ) -> AsyncGenerator[Event]:
        """Stream ``delta`` events, collecting fragments, within ``LLM_TIMEOUT_S``.

        Raises:
            AnswerError: ``llm_timeout`` or ``llm_unavailable``.
        """
        loop = asyncio.get_running_loop()
        deadline = loop.time() + settings.LLM_TIMEOUT_S
        stream = generator.stream(prompt)
        try:
            while True:
                remaining = max(0.0, deadline - loop.time())
                try:
                    fragment = await asyncio.wait_for(anext(stream), timeout=remaining)
                except StopAsyncIteration:
                    return
                fragments.append(fragment)
                yield Event("delta", {"text": fragment})
        except TimeoutError as exc:
            raise AnswerError("llm_timeout", "The answer took too long.") from exc
        except AnswerError:
            raise
        except Exception as exc:
            logger.warning("Answer generation failed", exc_info=True)
            raise AnswerError("llm_unavailable", "The answer service is unavailable.") from exc
        finally:
            await stream.aclose()  # type: ignore[attr-defined]

    async def _fail(self, run: _Run, code: str) -> None:
        """Store the assistant message as failed with ``error_code`` (answer cleared)."""
        if run.assistant is None:
            return
        usage = run.generator.usage if run.generator else None
        run.assistant.status = Message.Status.FAILED
        run.assistant.error_code = code
        run.assistant.answer = None
        if usage is not None:
            run.assistant.prompt_tokens = usage.prompt_tokens
            run.assistant.completion_tokens = usage.completion_tokens
            await self._quota.aadd_tokens(usage.total)
        await run.assistant.asave()

    async def _prompt(
        self,
        conversation: Conversation,
        question: Message,
        context: _Context,
        office: dict[str, Any] | None,
    ) -> Prompt:
        """Render the versioned prompt with context, office type and history."""
        history = await sync_to_async(recent_turns)(conversation, question)
        return render_prompt(
            version=settings.PROMPT_VERSION,
            language=Lang(question.language),
            question=question.text,
            context=context.blocks,
            history=history,
            office_type_label=office["office_type"]["label"] if office else None,
        )

    async def _finish(
        self,
        run: _Run,
        *,
        assistant: Message,
        generator: AnswerGenerator,
        prompt: Prompt,
        fragments: list[str],
        context: _Context,
        office: dict[str, Any] | None,
    ) -> Message:
        """Validate the streamed JSON, resolve citations and persist the answer.

        Raises:
            AnswerError: ``invalid_answer`` when the JSON does not fit the schema.
        """
        try:
            parsed = Answer.model_validate_json("".join(fragments))
        except ValidationError as exc:
            logger.warning("Invalid answer JSON", extra={"errors": exc.error_count()})
            raise AnswerError("invalid_answer", "The answer could not be read.") from exc
        usage = generator.usage
        details = {
            "model": generator.model_name,
            "prompt_version": prompt.version,
            "prompt_hash": prompt.sha256,
            "corpus_version": settings.CORPUS_VERSION,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "latency_ms": int((time.perf_counter() - run.started) * MS_PER_S),
            "retrieval_ms": run.retrieval_ms,
        }
        citations = resolve_citations(parsed, context.sources)
        if parsed.refused:
            office = None  # contract v1.7: the early office event was provisional
        saved = await sync_to_async(save_answer)(assistant, citations, context, office, details)
        await self._quota.aadd_tokens(usage.total)
        return saved

    async def _events(
        self, user: User, conversation: Conversation | None, text: str, run: _Run
    ) -> AsyncGenerator[Event]:
        """The happy path of :meth:`answer`; failures propagate as exceptions."""
        scrubbed = scrub(text)
        conversation, question, assistant = await self._open_turn(
            user, conversation, scrubbed, detect_language(scrubbed)
        )
        run.assistant = assistant
        await self._quota.aconsume(user.id)
        yield Event(
            "meta",
            {
                "conversation_id": str(conversation.id),
                "user_message_id": str(question.id),
                "assistant_message_id": str(assistant.id),
            },
        )
        yield Event("status", {"stage": "searching"})
        retrieval_started = time.perf_counter()
        hits = await self._retrieve(question.text, Lang(question.language))
        run.retrieval_ms = int((time.perf_counter() - retrieval_started) * MS_PER_S)
        context = await sync_to_async(build_context)(hits)
        yield Event("status", {"stage": "found", "source_count": len(context.blocks)})

        office = await sync_to_async(self._locate)(
            list(dict.fromkeys(hit.document_id for hit in context.hits)),
            district_id=user.district_id,
            region_id=user.region_id,
            lang=user.ui_language,
        )
        if office is not None:
            yield Event("office", office)
        yield Event("status", {"stage": "writing"})

        prompt = await self._prompt(conversation, question, context, office)
        generator = run.generator = self._generator_factory()
        fragments: list[str] = []
        deltas = self._generate(generator, prompt, fragments)
        try:
            async for event in deltas:
                yield event
        finally:
            await deltas.aclose()
        saved = await self._finish(
            run,
            assistant=assistant,
            generator=generator,
            prompt=prompt,
            fragments=fragments,
            context=context,
            office=office,
        )
        yield Event("final", {"message": await sync_to_async(serialize_message)(saved)})
        yield Event("done", {})

    async def answer(
        self, user: User, conversation: Conversation | None, text: str
    ) -> AsyncGenerator[Event]:
        """Answer one question as events: meta → status* → office? → delta* → final → done.

        Any failure after ``meta`` becomes one ``error`` event and a failed message. A client
        disconnect stores the message as failed with ``error_code="stopped"`` and no answer.
        The stream lock is taken first and always released. Losing the race for it (another
        answer started after :meth:`prepare`) ends the stream with one ``stream_in_progress``
        error event.

        Args:
            user: The signed-in user who passed :meth:`prepare`.
            conversation: The conversation to continue, or None.
            text: The raw question (scrubbed before anything else).
        """
        try:
            await self._quota.aacquire_stream(user.id)
        except StreamInProgress as exc:
            yield Event("error", {"code": exc.default_code, "message": str(exc.detail)})
            return
        run = _Run(started=time.perf_counter())
        events = self._events(user, conversation, text, run)
        try:
            async for event in events:
                yield event
        except asyncio.CancelledError, GeneratorExit:
            await self._fail(run, STOPPED)
            raise
        except AnswerError as exc:
            await self._fail(run, exc.code)
            yield Event("error", {"code": exc.code, "message": exc.message})
        except Exception:
            logger.exception("Answer failed")
            await self._fail(run, "internal_error")
            yield Event("error", {"code": "internal_error", "message": "Something went wrong."})
        finally:
            await events.aclose()
            await self._quota.arelease_stream(user.id)
