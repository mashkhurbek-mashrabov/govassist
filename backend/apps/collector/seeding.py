import json
from pathlib import Path

from apps.collector.constants import SAMPLE_MAX_PAGES, SAMPLE_SOURCES_FIXTURE, TERMS_NOTE
from apps.collector.models import CrawlSource


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
