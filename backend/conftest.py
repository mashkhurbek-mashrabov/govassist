"""Shared pytest fixtures."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from allauth.account.models import EmailAddress
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.geo.models import District, Region

TEST_PASSWORD = "correct-horse-battery-staple"


@pytest.fixture(autouse=True)
def _clear_cache() -> Iterator[None]:
    """Give every test empty counters and locks."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def _raw_data_dir(tmp_path: Path) -> Iterator[None]:
    """Write crawled bytes into a temp dir instead of ``data/``."""
    with override_settings(RAW_DATA_DIR=tmp_path / "raw"):
        yield


@pytest.fixture
def region(db: None) -> Region:
    """A region with SOATO-shaped data (test-only values)."""
    return Region.objects.create(
        id=9901,
        name_uz_latn="Test viloyati",
        name_uz_cyrl="Тест вилояти",
        name_ru="Тестовая область",
        name_en="Test region",
    )


@pytest.fixture
def district(region: Region) -> District:
    """A district inside ``region``."""
    return District.objects.create(
        id=9901201,
        region=region,
        name_uz_latn="Test tumani",
        name_uz_cyrl="Тест тумани",
        name_ru="Тестовый район",
        name_en="Test district",
    )


@pytest.fixture
def other_district(db: None) -> District:
    """A district in a different region."""
    other = Region.objects.create(
        id=9902,
        name_uz_latn="Boshqa viloyat",
        name_uz_cyrl="Бошқа вилоят",
        name_ru="Другая область",
        name_en="Other region",
    )
    return District.objects.create(
        id=9902201,
        region=other,
        name_uz_latn="Boshqa tuman",
        name_uz_cyrl="Бошқа туман",
        name_ru="Другой район",
        name_en="Other district",
    )


def make_user(email: str = "user@example.com", *, verified: bool = True, **extra: object) -> User:
    """Create a user with an allauth email record.

    Args:
        email: Login email.
        verified: Whether the email is verified.
        **extra: Other user fields (region, district, ...).
    """
    user = User.objects.create_user(email, TEST_PASSWORD, **extra)
    EmailAddress.objects.create(user=user, email=email, verified=verified, primary=True)
    return user


@pytest.fixture
def user(district: District) -> User:
    """A verified user with a complete profile."""
    return make_user(region=district.region, district=district)


@pytest.fixture
def api() -> APIClient:
    """An anonymous API client that enforces CSRF like a browser."""
    return APIClient(enforce_csrf_checks=False)


@pytest.fixture
def auth_api(api: APIClient, user: User) -> APIClient:
    """An API client logged in as ``user``."""
    api.force_authenticate(user)
    return api
