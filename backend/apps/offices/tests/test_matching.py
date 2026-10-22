"""Tests for district matching within a region."""

import pytest

from apps.geo.models import District, Region
from apps.offices.matching import match_district


@pytest.mark.django_db
def test_match_district_exact_latin_with_suffix(region: Region, district: District) -> None:
    """Verifies exact match on Latin name with administrative suffix."""
    match = match_district("Test tumani", region)
    assert match is not None
    assert match.district == district
    assert match.needs_review is False


@pytest.mark.django_db
def test_match_district_exact_latin_without_suffix(region: Region, district: District) -> None:
    """Verifies exact match on Latin name without administrative suffix."""
    match = match_district("Test", region)
    assert match is not None
    assert match.district == district
    assert match.needs_review is False


@pytest.mark.django_db
def test_match_district_exact_cyrillic(region: Region, district: District) -> None:
    """Verifies transliteration and exact match on Cyrillic input."""
    match = match_district("Тест тумани", region)
    assert match is not None
    assert match.district == district
    assert match.needs_review is False


@pytest.mark.django_db
def test_match_district_exact_russian(region: Region, district: District) -> None:
    """Verifies exact match against Russian name field."""
    match = match_district("Тестовый район", region)
    assert match is not None
    assert match.district == district
    assert match.needs_review is False


@pytest.mark.django_db
def test_match_district_fuzzy(region: Region) -> None:
    """Verifies fuzzy matching with ratio >= FUZZY_THRESHOLD flags needs_review."""
    long_district = District.objects.create(
        id=9901301,
        region=region,
        name_uz_latn="Shayxontohur tumani",
        name_uz_cyrl="Шайхонтоҳур тумани",
        name_ru="Шайхантахурский район",
        name_en="Shaykhontokhur district",
    )
    # One letter substitution in a long name: ratio 22/24 = 0.9167 >= 0.9
    match = match_district("Shayxontoxur tumani", region)
    assert match is not None
    assert match.district == long_district
    assert match.needs_review is True


@pytest.mark.django_db
def test_match_district_no_match(region: Region, district: District) -> None:
    """Verifies that dissimilar names return None."""
    match = match_district("Butunlay boshqa nom", region)
    assert match is None


@pytest.mark.django_db
def test_match_district_empty_or_whitespace(region: Region) -> None:
    """Verifies empty or whitespace inputs return None."""
    assert match_district("", region) is None
    assert match_district("   ", region) is None


@pytest.mark.django_db
def test_match_district_region_without_districts() -> None:
    """Verifies region with no districts returns None."""
    empty_region = Region.objects.create(
        id=9903,
        name_uz_latn="Boʻsh viloyat",
        name_uz_cyrl="Бўш вилоят",
        name_ru="Пустая область",
        name_en="Empty region",
    )
    assert match_district("Test", empty_region) is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("SAMARQAND shahri", 9904401),
        ("Samarqand shahar", 9904401),
        ("Samarqand tumani", 9904233),
        ("Самарқанд тумани", 9904233),
        ("Samarqand", None),  # city or district: ambiguous, never guessed
    ],
)
def test_match_district_tells_a_city_from_its_namesake_district(
    name: str, expected: int | None
) -> None:
    """SOATO names the city "Samarqand"; the suffix word picks city or district."""
    region = Region.objects.create(id=9904, name_uz_latn="Namuna viloyati")
    District.objects.create(id=9904401, region=region, name_uz_latn="Samarqand", kind="city")
    District.objects.create(
        id=9904233, region=region, name_uz_latn="Samarqand tumani", name_uz_cyrl="Самарқанд тумани"
    )
    match = match_district(name, region)
    assert (match.district.id if match else None) == expected
    assert match is None or match.needs_review is False
