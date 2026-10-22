"""Admin dashboard numbers (plan §13): knowledge, offices, questions, feedback, tokens."""

from dataclasses import dataclass

from django.conf import settings
from django.db.models import Count, Q

from apps.chat.limits import QuotaService, local_now
from apps.chat.models import Feedback, Message
from apps.common.constants import PERCENT, ReviewStatus
from apps.corpus.models import Chunk, Document
from apps.offices.models import Office


@dataclass(frozen=True)
class Kpi:
    """One dashboard tile."""

    title: str
    value: str
    footer: str
    progress: int | None = None


def _percent(part: int, whole: int) -> int:
    """Whole-number percentage, 0 when there is nothing to count."""
    return round(PERCENT * part / whole) if whole else 0


def dashboard_kpis(quota: QuotaService | None = None) -> list[Kpi]:
    """Compute the dashboard tiles.

    Args:
        quota: Token counter source (Redis in production).
    """
    documents = Document.objects.aggregate(
        approved=Count("id", filter=Q(status=ReviewStatus.APPROVED)),
        pending=Count("id", filter=Q(status=ReviewStatus.PENDING)),
    )
    chunks = Chunk.objects.aggregate(
        total=Count("id"), embedded=Count("id", filter=Q(embedding__isnull=False))
    )
    pending_offices = Office.objects.filter(status=ReviewStatus.PENDING).count()
    today = local_now().replace(hour=0, minute=0, second=0, microsecond=0)
    questions_today = Message.objects.filter(role=Message.Role.USER, created_at__gte=today).count()
    feedback = Feedback.objects.aggregate(total=Count("id"), up=Count("id", filter=Q(rating=1)))
    tokens = (quota or QuotaService()).tokens_today()
    cap = settings.GLOBAL_DAILY_TOKEN_CAP
    embedded = _percent(chunks["embedded"], chunks["total"])
    return [
        Kpi(
            "Documents",
            f"{documents['approved']} approved",
            f"{documents['pending']} pending review",
        ),
        Kpi(
            "Chunks embedded",
            f"{embedded}%",
            f"{chunks['embedded']} of {chunks['total']}",
            embedded,
        ),
        Kpi("Offices", f"{pending_offices} pending", "awaiting review"),
        Kpi("Questions today", str(questions_today), "Asia/Tashkent day"),
        Kpi(
            "Thumbs up",
            f"{_percent(feedback['up'], feedback['total'])}%",
            f"of {feedback['total']} ratings",
        ),
        Kpi("Tokens today", f"{tokens:,}", f"cap {cap:,}", _percent(tokens, cap)),
    ]
