from django.db import models

from apps.common.models import BaseModel
from apps.evaluation.constants import RunKind


class EvalRun(BaseModel):
    """One scripted evaluation run (or one imported set of external chatbot answers).

    ``config`` holds the ablation switches (mode, normalize, rag, prompt) or, for an external
    run, the system, prompt style and date; ``model_names`` names every model used.
    """

    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=10, choices=RunKind, default=RunKind.GOVASSIST)
    question_version = models.CharField(max_length=20)
    config = models.JSONField(default=dict)
    corpus_version = models.CharField(max_length=20, blank=True)
    prompt_version = models.CharField(max_length=20, blank=True)
    git_sha = models.CharField(max_length=40, blank=True)
    model_names = models.JSONField(default=dict)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name
