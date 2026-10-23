from datetime import datetime, timedelta
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.chat.constants import TITLE_FROM_QUESTION_CHARS, MessageErrorCode
from apps.chat.models import Conversation, Feedback, Message
from apps.common.constants import Lang
from apps.common.pii import scrub


@transaction.atomic
def upsert_feedback(message: Message, *, rating: int, comment: str) -> tuple[Feedback, bool]:
    """Create or replace the feedback on an assistant message.

    Args:
        message: The assistant message.
        rating: 1 or -1.
        comment: Optional comment (already length-checked); PII is scrubbed before storage.

    Returns:
        The feedback and whether it was created.
    """
    return Feedback.objects.update_or_create(
        message=message, defaults={"rating": rating, "comment": scrub(comment)}
    )


def delete_conversation(conversation: Conversation) -> None:
    """Delete a conversation with its messages, retrievals and feedback.

    Args:
        conversation: The conversation to delete.
    """
    conversation.delete()


@transaction.atomic
def open_turn(
    user: User, conversation: Conversation | None, text: str, lang: Lang
) -> tuple[Conversation, Message, Message]:
    """Create the conversation (if new), the user message and the streaming answer together.

    One transaction: a crash can no longer leave a question without its answer row, or a
    new conversation without its question.

    Args:
        user: The asking user.
        conversation: The conversation to continue, or None for a new one.
        text: The scrubbed question.
        lang: The question's language.

    Returns:
        The conversation, the user message and the ``streaming`` assistant message.
    """
    if conversation is None:
        title = text[:TITLE_FROM_QUESTION_CHARS].strip()
        conversation = Conversation.objects.create(user=user, language=lang, title=title)
    else:
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=["updated_at"])
    question = Message.objects.create(
        conversation=conversation, role=Message.Role.USER, text=text, language=lang
    )
    assistant = Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        status=Message.Status.STREAMING,
        language=lang,
    )
    return conversation, question, assistant


def expire_stale_streams(
    *, conversation_id: UUID | None = None, now: datetime | None = None
) -> int:
    """Mark ``streaming`` answers older than the stream lock TTL as failed (``stopped``).

    No live stream outlives its lock, so an older ``streaming`` row belongs to a process that
    died (worker restart, crash) and would otherwise show as "writing…" forever.

    Args:
        conversation_id: Limit to one conversation (the cheap read-time check).
        now: The current time (tests).

    Returns:
        How many rows were marked.
    """
    cutoff = (now or timezone.now()) - timedelta(seconds=settings.STREAM_LOCK_TTL_S)
    stale = Message.objects.filter(status=Message.Status.STREAMING, created_at__lt=cutoff)
    if conversation_id is not None:
        stale = stale.filter(conversation_id=conversation_id)
    return stale.update(status=Message.Status.FAILED, error_code=MessageErrorCode.STOPPED)
