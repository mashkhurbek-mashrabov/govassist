from django.db import models

from apps.common.constants import Lang
from apps.common.models import BaseModel
from apps.evaluation.constants import Category, Script


class EvalQuestion(BaseModel):
    """One test question of a versioned question set (plan §7).

    ``district`` is the asker's district (office-routing questions give one); ``group_id`` ties
    the same question across languages and scripts for paired comparisons.
    """

    qid = models.CharField(max_length=50)
    version = models.CharField(max_length=20)
    question = models.TextField()
    language = models.CharField(max_length=8, choices=Lang)
    script = models.CharField(max_length=4, choices=Script)
    group_id = models.CharField(max_length=50)
    category = models.CharField(max_length=20, choices=Category)
    expected_facts = models.JSONField(default=list, blank=True)
    expected_doc_ids = models.JSONField(default=list, blank=True)
    expected_office_type = models.CharField(max_length=40, blank=True)
    district = models.ForeignKey(
        "geo.District", null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    in_corpus = models.BooleanField(default=True)

    class Meta:
        ordering = ["version", "qid"]
        constraints = [
            models.UniqueConstraint(fields=["version", "qid"], name="uniq_eval_question"),
        ]

    def __str__(self) -> str:
        return f"{self.version}/{self.qid}"
