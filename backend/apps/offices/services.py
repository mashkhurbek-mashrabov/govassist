"""Office review and approval lifecycle services."""

from django.db import transaction
from django.db.models import QuerySet

from apps.common.models import ReviewStatus
from apps.offices.models import Office


@transaction.atomic
def approve_offices(queryset: QuerySet[Office]) -> int:
    """Approve physical offices for citizen district recommendations.

    Args:
        queryset: QuerySet of Office instances to approve.

    Returns:
        Number of offices updated.
    """
    return queryset.update(status=ReviewStatus.APPROVED)


@transaction.atomic
def reject_offices(queryset: QuerySet[Office]) -> int:
    """Reject physical offices so they are excluded from citizen recommendations.

    Args:
        queryset: QuerySet of Office instances to reject.

    Returns:
        Number of offices updated.
    """
    return queryset.update(status=ReviewStatus.REJECTED)
