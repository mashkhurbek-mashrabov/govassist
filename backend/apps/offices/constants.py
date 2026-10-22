"""Constants of the offices app (AGENTS.md: no constant values elsewhere in the app)."""

import re
from pathlib import Path

TIME_REGEX = r"^(?:[01]\d|2[0-3]):[0-5]\d$"

MAPS_SEARCH_BASE_URL = "https://www.google.com/maps/search/?api=1&query="

FUZZY_THRESHOLD = 0.9

DISTRICT_SUFFIXES = (
    "tumani",
    "tuman",
    "shahri",
    "shahar",
    "rayon",
    "gorod",
    "district",
    "city",
    "район",
    "город",
)

SUFFIX_REGEX = re.compile(
    r"\s+(?:"
    + "|".join(re.escape(s) for s in sorted(DISTRICT_SUFFIXES, key=len, reverse=True))
    + r")$",
    re.IGNORECASE,
)

OFFICE_TYPES_FIXTURE = Path(__file__).parent / "fixtures" / "office_types.json"
