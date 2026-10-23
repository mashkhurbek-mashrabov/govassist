"""Fill office phones from already saved pages (worker image: needs the parsers).

No request is made: the number is read from the structured data of the page bytes the crawl
stored under ``RAW_DATA_DIR``. Used for goldenpages.uz, which blocks automated access.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from django.db import transaction

from apps.collector.fetchers import FetchResult
from apps.collector.models import RawPage
from apps.collector.parsers import parse
from apps.offices.models import Office

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BackfillResult:
    """What a phone backfill did."""

    checked: int
    filled: int
    no_raw_page: int
    no_phone: int


def _saved_phone(url: str) -> str | None:
    """The phone in the newest saved copy of ``url``; None when there is none or no number.

    Raises:
        FileNotFoundError: When the stored path is gone (reported by the caller).
    """
    raw = RawPage.objects.filter(url=url).order_by("-fetched_at").first()
    if raw is None:
        raise FileNotFoundError(url)
    body = Path(raw.raw_path).read_bytes()
    page = parse(
        FetchResult(
            url=url, final_url=url, status=raw.http_status, content_type=raw.content_type, body=body
        )
    )
    office = page.offices[0] if page.offices else None
    return office.phone if office else None


@transaction.atomic
def backfill_phones(publisher: str, *, dry_run: bool = False) -> BackfillResult:
    """Set ``phone`` on a publisher's offices that have none, from their saved pages.

    Args:
        publisher: The source publisher, e.g. ``goldenpages.uz``.
        dry_run: Count only; change nothing.

    Returns:
        The counts.
    """
    offices = list(Office.objects.filter(source__publisher=publisher, phone__isnull=True))
    filled = missing = without = 0
    for office in offices:
        try:
            phone = _saved_phone(office.source_url)
        except FileNotFoundError:
            missing += 1
            logger.warning("No saved page for office", extra={"url": office.source_url})
            continue
        if phone is None:
            without += 1
            continue
        filled += 1
        if not dry_run:
            office.phone = phone
            office.save(update_fields=["phone", "updated_at"])
    return BackfillResult(
        checked=len(offices), filled=filled, no_raw_page=missing, no_phone=without
    )
