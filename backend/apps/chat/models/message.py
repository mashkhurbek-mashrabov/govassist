from django.db import models

from apps.chat.constants import MessageRole, MessageStatus
from apps.chat.models.conversation import Conversation
from apps.common.constants import Lang
from apps.common.models import BaseModel


class Message(BaseModel):
    """A user question (scrubbed text) or an assistant answer with its run metadata."""

    Role = MessageRole

    Status = MessageStatus

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=Role)
    text = models.TextField(blank=True)
    answer = models.JSONField(null=True, blank=True)
    sources = models.JSONField(default=list, blank=True)
    office_match = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status, default=Status.COMPLETE)
    refused = models.BooleanField(default=False)
    error_code = models.CharField(max_length=40, blank=True)
    language = models.CharField(max_length=8, choices=Lang, default=Lang.UZ_LATN)
    model = models.CharField(max_length=80, blank=True)
    prompt_version = models.CharField(max_length=20, blank=True)
    prompt_hash = models.CharField(max_length=64, blank=True)
    corpus_version = models.CharField(max_length=20, blank=True)
    prompt_tokens = models.PositiveIntegerField(null=True, blank=True)
    completion_tokens = models.PositiveIntegerField(null=True, blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    retrieval_ms = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.role} {self.id}"
