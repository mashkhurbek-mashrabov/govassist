from django.db import transaction

from apps.chat.models import Conversation, Feedback, Message
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
