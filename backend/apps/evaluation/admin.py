from django.contrib import admin

from apps.common.admin import BaseAdmin
from apps.evaluation.models import EvalQuestion, EvalResult, EvalRun


@admin.register(EvalQuestion)
class EvalQuestionAdmin(BaseAdmin):
    """Test questions per version."""

    list_display = ("qid", "version", "category", "language", "script", "in_corpus")
    list_filter = ("version", "category", "language", "script", "in_corpus")
    search_fields = ("qid", "question", "group_id")


@admin.register(EvalRun)
class EvalRunAdmin(BaseAdmin):
    """Evaluation runs (read-only: results come only from scripted runs)."""

    list_display = (
        "name",
        "kind",
        "question_version",
        "prompt_version",
        "started_at",
        "finished_at",
    )
    list_filter = ("kind", "question_version", "prompt_version")
    readonly_fields = tuple(field.name for field in EvalRun._meta.fields)

    def has_add_permission(self, request: object) -> bool:
        """Runs are created by ``run_eval`` / ``import_external_answers`` only."""
        return False


@admin.register(EvalResult)
class EvalResultAdmin(BaseAdmin):
    """Per-question results (read-only)."""

    list_select_related = ("run", "question")
    list_display = ("run", "question", "error", "latency_ms")
    list_filter = ("run", "error")
    readonly_fields = tuple(field.name for field in EvalResult._meta.fields)

    def has_add_permission(self, request: object) -> bool:
        """Results are created by the evaluation commands only."""
        return False
