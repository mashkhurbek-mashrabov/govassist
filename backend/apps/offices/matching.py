"""District matching for office ingestion."""

import difflib
from dataclasses import dataclass

from apps.common.text import canonicalize, detect_script, uz_cyrl_to_latn
from apps.geo.models import District, Region
from apps.offices.constants import FUZZY_THRESHOLD, SUFFIX_REGEX


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


def match_district(name: str, region: Region) -> DistrictMatch | None:
    """Match a district name to a District within the given Region.

    Steps:
      1. If Cyrillic, transliterate with ``uz_cyrl_to_latn``.
      2. Canonicalize text (lowercase, unified apostrophes, whitespace).
      3. Strip administrative suffixes (tumani, tuman, shahri, etc.).
      4. Exact match against all 4 localized name fields of districts in region.
      5. Fuzzy match with SequenceMatcher (ratio >= FUZZY_THRESHOLD).
      6. Return None if no match meets the threshold.

    Args:
        name: Extracted district name string.
        region: Region to constrain the search to.

    Returns:
        DistrictMatch with needs_review flag, or None if unmatchable.
    """
    if not name or not name.strip():
        return None

    cleaned_name = _normalize_name(name)
    if not cleaned_name:
        return None

    districts = list(region.districts.all())
    if not districts:
        return None

    # Step 4: Exact match against any of the 4 name fields (normalized)
    for district in districts:
        for field_name in ("name_uz_latn", "name_uz_cyrl", "name_ru", "name_en"):
            val: str = getattr(district, field_name, "")
            if not val:
                continue
            if cleaned_name == _normalize_name(val):
                return DistrictMatch(district=district, needs_review=False)

    # Step 5: Fuzzy match using difflib.SequenceMatcher
    best_district: District | None = None
    best_ratio = 0.0

    for district in districts:
        for field_name in ("name_uz_latn", "name_uz_cyrl", "name_ru", "name_en"):
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
