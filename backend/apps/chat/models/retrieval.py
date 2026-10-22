from django.db import models

from apps.chat.models.message import Message
from apps.common.models import BaseModel


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
