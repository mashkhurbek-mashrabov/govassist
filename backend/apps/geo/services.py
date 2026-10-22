import json
from pathlib import Path
from typing import Any

from django.db import transaction

from apps.geo.models import District, Region

SOATO_FIXTURE = Path(__file__).parent / "fixtures" / "soato.json"
NAME_FIELDS = ("name_uz_latn", "name_uz_cyrl", "name_ru")


def _names(row: dict[str, Any]) -> dict[str, str]:
    """Return the localized name fields; English falls back to the official Latin name.

    Args:
        row: One region or district row from the fixture.
    """
    names = {field: row[field] for field in NAME_FIELDS}
    names["name_en"] = row.get("name_en") or row["name_uz_latn"]
    return names


@transaction.atomic
def seed_geo(path: Path = SOATO_FIXTURE) -> tuple[int, int]:
    """Upsert regions and districts from the official SOATO fixture.

    Args:
        path: The fixture file (see ``docs/corpus-sources.md`` for its origin).

    Returns:
        (regions, districts) written.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    for row in data["regions"]:
        Region.objects.update_or_create(id=row["id"], defaults=_names(row))
    for row in data["districts"]:
        District.objects.update_or_create(
            id=row["id"],
            defaults={"region_id": row["region_id"], "kind": row["kind"], **_names(row)},
        )
    return len(data["regions"]), len(data["districts"])
