from django.db import models

from apps.common.models import BaseModel
from apps.evaluation.models.question import EvalQuestion
from apps.evaluation.models.run import EvalRun


class EvalResult(BaseModel):
    """One question answered (or imported) in one run, with its scores.

    ``answer`` is the validated Answer (or ``{"text": ...}`` for an external transcript);
    ``scores`` holds every metric key from ``constants`` (None when not applicable).
    """

    run = models.ForeignKey(EvalRun, on_delete=models.CASCADE, related_name="results")
    question = models.ForeignKey(EvalQuestion, on_delete=models.PROTECT, related_name="results")
    answer = models.JSONField(null=True, blank=True)
    error = models.CharField(max_length=40, blank=True)
    retrieved_doc_ids = models.JSONField(default=list, blank=True)
    cited_doc_ids = models.JSONField(default=list, blank=True)
    office_match = models.JSONField(null=True, blank=True)
    scores = models.JSONField(default=dict, blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    prompt_tokens = models.PositiveIntegerField(null=True, blank=True)
    completion_tokens = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["run", "question"]
        constraints = [
            models.UniqueConstraint(fields=["run", "question"], name="uniq_eval_result"),
        ]

    def __str__(self) -> str:
        return f"{self.run_id}:{self.question_id}"
