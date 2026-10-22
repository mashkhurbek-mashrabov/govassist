import json
from pathlib import Path

from apps.offices.constants import OFFICE_TYPES_FIXTURE
from apps.offices.models import OfficeType


def seed_office_types(path: Path = OFFICE_TYPES_FIXTURE) -> int:
    """Upsert the initial office types of contract §5 (codes + UI labels).

    Args:
        path: The fixture file.

    Returns:
        Number of office types written.
    """
    rows = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        OfficeType.objects.update_or_create(code=row.pop("code"), defaults=row)
    return len(rows)
