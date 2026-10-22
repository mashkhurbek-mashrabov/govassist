from uuid import UUID

from django.db.models import OuterRef, Prefetch, QuerySet, Subquery
from django.db.models.functions import Left

from apps.accounts.models import User
from apps.chat.constants import PREVIEW_CHARS
from apps.chat.models import Conversation, Message


def conversations_of(user: User) -> QuerySet[Conversation]:
    """The user's conversations, newest first, with ``last_message_preview``.

    Args:
        user: The owner.
    """
    last_question = (
        Message.objects.filter(conversation=OuterRef("pk"), role=Message.Role.USER)
        .order_by("-created_at")
        .values("text")[:1]
    )
    return (
        Conversation.objects.filter(user=user)
        .annotate(last_message_preview=Left(Subquery(last_question), PREVIEW_CHARS))
        .order_by("-updated_at")
    )


def conversation_with_messages(user: User, conversation_id: UUID) -> Conversation | None:
    """One of the user's conversations with messages and feedback loaded, or None.

    Args:
        user: The owner.
        conversation_id: The conversation id.
    """
    messages = Message.objects.select_related("feedback").order_by("created_at")
    return (
        Conversation.objects.filter(user=user, id=conversation_id)
        .prefetch_related(Prefetch("messages", queryset=messages))
        .first()
    )


def assistant_message_of(user: User, message_id: UUID) -> Message | None:
    """An assistant message in one of the user's conversations, or None.

    Args:
        user: The owner.
        message_id: The message id.
    """
    return Message.objects.filter(
        id=message_id, role=Message.Role.ASSISTANT, conversation__user=user
    ).first()
