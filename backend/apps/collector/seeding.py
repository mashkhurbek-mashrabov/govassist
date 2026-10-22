import json
from pathlib import Path

from django.db import transaction

from apps.collector.constants import (
    DIRECTORY_FOLLOW,
    DIRECTORY_SOURCES_FIXTURE,
    DIRECTORY_TERMS_NOTE,
    SAMPLE_MAX_PAGES,
    SAMPLE_SOURCES_FIXTURE,
    TERMS_NOTE,
)
from apps.collector.fetchers import host_of
from apps.collector.models import CrawlSource
from apps.geo.models import Region
from apps.offices.models import OfficeType


def seed_sample_sources(path: Path = SAMPLE_SOURCES_FIXTURE) -> int:
    """Create the real, robots-allowed sample sources (one page each, no link following).

    Args:
        path: The fixture file (every URL is recorded in docs/corpus-sources.md).

    Returns:
        Number of sources written.
    """
    rows = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        CrawlSource.objects.update_or_create(
            start_url=row["start_url"],
            defaults={
                "name": row["name"],
                "kind": CrawlSource.Kind.DOCUMENT,
                "document_kind": row["document_kind"],
                "publisher": row["publisher"],
                "max_pages": SAMPLE_MAX_PAGES,
                "allowed_url_pattern": "",
                "terms_note": TERMS_NOTE,
            },
        )
    return len(rows)


@transaction.atomic
def seed_directory_sources(path: Path = DIRECTORY_SOURCES_FIXTURE) -> int:
    """Create the office sources from business directories (goldenpages.uz, yellowpages.uz).

    Each is one rubric listing for one office type, limited to its regions and an optional
    name pattern. Run after the geo and office-type seeds.

    Args:
        path: The fixture file (every site is recorded in docs/corpus-sources.md).

    Returns:
        Number of sources written.

    Raises:
        OfficeType.DoesNotExist: When an office type code is not seeded.
    """
    rows = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        host = host_of(row["start_url"]).removeprefix("www.")
        source, _ = CrawlSource.objects.update_or_create(
            start_url=row["start_url"],
            defaults={
                "name": row["name"],
                "kind": CrawlSource.Kind.OFFICE,
                "office_type": OfficeType.objects.get(code=row["office_type"]),
                "office_name_pattern": row["name_pattern"],
                "publisher": host,
                "max_pages": row["max_pages"],
                "allowed_url_pattern": DIRECTORY_FOLLOW[host],
                "terms_note": DIRECTORY_TERMS_NOTE,
            },
        )
        source.office_regions.set(Region.objects.filter(id__in=row["regions"]))
    return len(rows)
