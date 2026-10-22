"""Shared pytest fixtures."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from allauth.account.models import EmailAddress
from asgiref.sync import async_to_sync
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.common.i18n import Lang
from apps.common.models import ReviewStatus
from apps.common.text import normalize_for_search
from apps.corpus.embeddings import FakeEmbedder
from apps.corpus.models import Chunk, Document
from apps.geo.models import District, Region
from apps.offices.models import Office, OfficeType, ServiceOffice

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


PASSPORT_TEXT = "NAMUNA pasportni almashtirish uchun ariza topshiriladi va boj toʻlanadi."


def namuna_document(text: str, *, kind: str = "service_page", slug: str = "passport") -> Document:
    """An approved NAMUNA document with one embedded chunk."""
    document = Document.objects.create(
        kind=kind,
        title=f"NAMUNA {slug}",
        url=f"https://example.org/{slug}",
        publisher="example.org",
        fetched_at=timezone.now(),
        text=text,
        text_hash="x",
        corpus_version="test",
        status=ReviewStatus.APPROVED,
        section_label="NAMUNA-1",
    )
    Chunk.objects.create(
        document=document,
        order=0,
        heading_path="1-bob › 2-modda",
        text=text,
        char_count=len(text),
        text_normalized=normalize_for_search(text, Lang.UZ_LATN),
        embedding=async_to_sync(FakeEmbedder().embed_query)(text),
    )
    return document


@pytest.fixture
def office_type(db: None) -> OfficeType:
    """The NAMUNA public service centre type."""
    return OfficeType.objects.create(
        code="public_service_center",
        name_uz_latn="Davlat xizmatlari markazi",
        name_uz_cyrl="Давлат хизматлари маркази",
        name_ru="Центр госуслуг",
        name_en="Public service centre",
    )


@pytest.fixture
def passport_doc(office_type: OfficeType) -> Document:
    """The passport service page, mapped (confirmed) to the office type."""
    document = namuna_document(PASSPORT_TEXT)
    ServiceOffice.objects.create(document=document, office_type=office_type, confirmed=True)
    return document


def make_office(office_type: OfficeType, district: District, **extra: Any) -> Office:
    """An approved NAMUNA office in ``district``."""
    defaults: dict[str, Any] = {
        "name": f"NAMUNA {district.name_uz_latn} markazi",
        "address": "NAMUNA koʻchasi, 1-uy",
        "source_url": "https://example.org/offices",
        "data_as_of": timezone.localdate(),
        "status": ReviewStatus.APPROVED,
        "working_hours": [
            {
                "days": ["mon", "tue"],
                "open": "09:00",
                "close": "18:00",
                "break": {"start": "13:00", "end": "14:00"},
            },
        ],
    }
    return Office.objects.create(
        office_type=office_type,
        district=district,
        region=district.region,
        **(defaults | extra),
    )


def answer_json(**overrides: Any) -> str:
    """A NAMUNA service answer citing S1 (and an unknown S7)."""
    answer: dict[str, Any] = {
        "answer_type": "service",
        "language": "uz-Latn",
        "title": "NAMUNA pasport",
        "summary": "NAMUNA xulosa.",
        "steps": [{"text": "NAMUNA ariza", "source_ids": ["S1", "S7"]}],
        "documents": [],
        "fee": None,
        "processing_time": None,
        "law_points": [],
        "follow_up_questions": [],
    }
    return json.dumps(answer | overrides, ensure_ascii=False)
