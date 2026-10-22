"""District matching for office ingestion."""

import difflib
from dataclasses import dataclass

from apps.common.text import canonicalize, detect_script, uz_cyrl_to_latn
from apps.geo.constants import DistrictKind
from apps.geo.models import District, Region
from apps.offices.constants import (
    CITY_SUFFIXES,
    DISTRICT_FIELDS,
    DISTRICT_KIND_SUFFIXES,
    FUZZY_THRESHOLD,
    SUFFIX_REGEX,
)


@dataclass(frozen=True)
class DistrictMatch:
    """Result of matching a district name string against official records."""

    district: District
    needs_review: bool


def _strip_suffixes(text: str) -> str:
    """Remove trailing district or city administrative suffixes.

    Args:
        text: Normalized district name.

    Returns:
        District name with administrative suffix removed.
    """
    return SUFFIX_REGEX.sub("", text).strip()


def _normalize_name(name: str) -> str:
    """Normalize input or DB name: transliterate Cyrillic, canonicalize, strip suffix.

    Args:
        name: Raw district name in any language or script.

    Returns:
        Stripped, lowercased, and canonicalized name.
    """
    if detect_script(name) == "cyrl":
        name = uz_cyrl_to_latn(name)
    canon = canonicalize(name)
    return _strip_suffixes(canon)


def _kind_of(name: str) -> str | None:
    """``city`` or ``district`` when the name ends with a word saying which, else None."""
    words = canonicalize(uz_cyrl_to_latn(name) if detect_script(name) == "cyrl" else name).split()
    last = words[-1] if words else ""
    if last in CITY_SUFFIXES:
        return DistrictKind.CITY
    if last in DISTRICT_KIND_SUFFIXES:
        return DistrictKind.DISTRICT
    return None


def match_district(name: str, region: Region) -> DistrictMatch | None:
    """Match a district name to a District within the given Region.

    Steps:
      1. If Cyrillic, transliterate with ``uz_cyrl_to_latn``.
      2. Canonicalize text (lowercase, unified apostrophes, whitespace).
      3. Strip administrative suffixes (tumani, tuman, shahri, etc.).
      4. Exact match against all 4 localized name fields of districts in region; several
         hits are narrowed by the suffix's kind (city/district), else ambiguous (None).
      5. Fuzzy match with SequenceMatcher (ratio >= FUZZY_THRESHOLD).
      6. Return None if no match meets the threshold.

    Args:
        name: Extracted district name string.
        region: Region to constrain the search to.

    Returns:
        DistrictMatch with needs_review flag, or None if unmatchable.
    """
    cleaned_name = _normalize_name(name)
    if not cleaned_name:  # empty, whitespace or only a suffix word
        return None

    districts = list(region.districts.all())
    if not districts:
        return None

    # Step 4: exact match on any of the 4 name fields (normalized). When the stripped name
    # fits several units (the city "Samarqand" and "Samarqand tumani"), the suffix word of
    # the input picks the kind; still several means ambiguous, and nothing is guessed.
    exact = [
        district
        for district in districts
        if any(
            cleaned_name == _normalize_name(value)
            for field in DISTRICT_FIELDS
            if (value := getattr(district, field, ""))
        )
    ]
    kind = _kind_of(name)
    if len(exact) > 1 and kind is not None:
        exact = [district for district in exact if district.kind == kind]
    if len(exact) == 1:
        return DistrictMatch(district=exact[0], needs_review=False)
    if exact:
        return None

    # Step 5: Fuzzy match using difflib.SequenceMatcher
    best_district: District | None = None
    best_ratio = 0.0

    for district in districts:
        for field_name in DISTRICT_FIELDS:
            val = getattr(district, field_name, "")
            if not val:
                continue
            ratio = difflib.SequenceMatcher(None, cleaned_name, _normalize_name(val)).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_district = district

    if best_district is not None and best_ratio >= FUZZY_THRESHOLD:
        return DistrictMatch(district=best_district, needs_review=True)

    return None
