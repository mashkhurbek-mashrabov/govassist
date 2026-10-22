from django.db.models import Count, IntegerField, OuterRef, Q, QuerySet, Subquery
from django.db.models.functions import Coalesce

from apps.collector.models import CrawlSource
from apps.common.models import ReviewStatus
from apps.offices.models import Office


def _approved_office_count() -> Coalesce:
    """Subquery: approved, active offices listed by the outer source."""
    offices = (
        Office.objects.filter(source=OuterRef("pk"), status=ReviewStatus.APPROVED, is_active=True)
        .values("source")
        .annotate(count=Count("id"))
        .values("count")
    )
    return Coalesce(Subquery(offices, output_field=IntegerField()), 0)


def public_sources() -> QuerySet[CrawlSource]:
    """Active sources that feed at least one approved document or office (About page).

    Rows are annotated with ``document_count`` and ``office_count``.
    """
    approved_documents = Q(documents__status=ReviewStatus.APPROVED, documents__is_active=True)
    return (
        CrawlSource.objects.filter(is_active=True)
        .annotate(
            document_count=Count("documents", filter=approved_documents),
            office_count=_approved_office_count(),
        )
        .filter(Q(document_count__gt=0) | Q(office_count__gt=0))
        .order_by("publisher", "name")
    )
