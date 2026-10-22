from django.conf import settings
from django.db import models

from apps.common.i18n import Lang
from apps.common.models import BaseModel


class Conversation(BaseModel):
    """A thread of questions and answers owned by one user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations"
    )
    title = models.CharField(max_length=120, blank=True)
    language = models.CharField(max_length=8, choices=Lang, default=Lang.UZ_LATN)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title or str(self.id)


class Message(BaseModel):
    """A user question (scrubbed text) or an assistant answer with its run metadata."""

    class Role(models.TextChoices):
        """Who wrote the message."""

        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    class Status(models.TextChoices):
        """Assistant message lifecycle."""

        STREAMING = "streaming", "Streaming"
        COMPLETE = "complete", "Complete"
        FAILED = "failed", "Failed"

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


class Retrieval(BaseModel):
    """One chunk shown to the model for an answer, with its scores (for evaluation)."""

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="retrievals")
    chunk = models.ForeignKey(
        "corpus.Chunk", null=True, on_delete=models.SET_NULL, related_name="+"
    )
    label = models.CharField(max_length=8)
    rank = models.PositiveSmallIntegerField()
    vector_score = models.FloatField(null=True)
    keyword_score = models.FloatField(null=True)
    fused_score = models.FloatField()
    cited = models.BooleanField(default=False)

    class Meta:
        ordering = ["message", "rank"]

    def __str__(self) -> str:
        return f"{self.message_id} {self.label}"


class Feedback(BaseModel):
    """A thumbs up/down on an assistant message."""

    class Rating(models.IntegerChoices):
        """Thumbs up or down."""

        UP = 1, "Up"
        DOWN = -1, "Down"

    message = models.OneToOneField(Message, on_delete=models.CASCADE, related_name="feedback")
    rating = models.SmallIntegerField(choices=Rating)
    comment = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.message_id}: {self.rating}"
