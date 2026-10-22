"""What a parsed page becomes: a pending Document, or pending Offices (plan §5 step 3)."""

import difflib
import hashlib
import logging
import math
import re
from datetime import datetime
from typing import Protocol

from django.conf import settings
from django.db import transaction

from apps.collector.constants import (
    EARTH_RADIUS_M,
    NAME_PARENTHESES,
    OFFICE_DUPLICATE_METRES,
    OFFICE_NAME_SIMILARITY,
    REGION_NAME_FIELDS,
    REGION_WORDS,
)
from apps.collector.extraction import (
    ListedOffice,
    OfficeCandidate,
    OfficeExtractor,
    OfficeTypeClassifier,
)
from apps.collector.models import CrawlSource
from apps.collector.parsers import ParsedPage
from apps.common.constants import ReviewStatus
from apps.common.text import canonicalize, detect_language, detect_script, uz_cyrl_to_latn
from apps.corpus.constants import DocumentKind
from apps.corpus.models import Document
from apps.geo.models import Region
from apps.offices.matching import DistrictMatch, match_district
from apps.offices.models import Office, OfficeType, ServiceOffice

logger = logging.getLogger(__name__)


class Pipeline(Protocol):
    """Processes one parsed page of a source."""

    def process(
        self, source: CrawlSource, page: ParsedPage, *, url: str, fetched_at: datetime
    ) -> None:
        """Turn ``page`` into pending rows for admin review."""
        ...


def _region_key(name: str) -> str:
    """Comparable region name: Latin, canonical, without 'viloyati'/'region'-like words."""
    return " ".join(REGION_WORDS.sub(" ", _latin(name)).split())


def _latin(name: str) -> str:
    """Canonical Latin form of a place name (Cyrillic transliterated)."""
    return canonicalize(uz_cyrl_to_latn(name) if detect_script(name) == "cyrl" else name)


def find_regions(name: str) -> list[Region]:
    """Regions ``name`` can mean, best first.

    A full-name match ("Toshkent viloyati") is unambiguous and returned alone. Otherwise every
    region whose name matches without 'viloyati'/'shahri' words is returned: "Toshkent" means
    both Tashkent city and Tashkent region, and the caller decides by scope and district.

    Args:
        name: Region name as written on the page.
    """
    full, key = _latin(name), _region_key(name)
    if not key:
        return []
    regions = list(Region.objects.all())
    names = {
        region.id: [getattr(region, field) for field in REGION_NAME_FIELDS] for region in regions
    }
    exact = [r for r in regions if any(_latin(n) == full for n in names[r.id] if n)]
    if exact:
        return exact
    return [r for r in regions if any(_region_key(n) == key for n in names[r.id] if n)]


def _resolve_place(
    candidate: OfficeCandidate, scope: list[Region]
) -> tuple[Region, DistrictMatch] | None:
    """The one region + district an office is in, or None when unknown or ambiguous.

    Candidate regions come from the stated region name, limited to the source's scope; with
    no usable region name, the scope itself. The district decides between them: an exact
    district match beats a fuzzy one, and two equally good matches are ambiguous.

    Args:
        candidate: The office as listed.
        scope: The source's regions (empty: every region).
    """
    regions = find_regions(candidate.region_name)
    if scope:
        allowed = {region.id for region in scope}
        regions = [r for r in regions if r.id in allowed] if regions else list(scope)
    matches = [
        (region, found)
        for region in regions
        if (found := match_district(candidate.district_name, region)) is not None
    ]
    exact = [pair for pair in matches if not pair[1].needs_review]
    best = exact or matches
    return best[0] if len(best) == 1 else None


def _name_key(name: str) -> str:
    """An office name without its parenthesised part, punctuation and case (duplicate checks)."""
    return canonicalize(NAME_PARENTHESES.sub(" ", name))


def same_name(a: str, b: str) -> bool:
    """True when two listed names are the same office name, give or take a suffix letter.

    Args:
        a: One name.
        b: The other.
    """
    first, second = _name_key(a), _name_key(b)
    return difflib.SequenceMatcher(None, first, second).ratio() >= OFFICE_NAME_SIMILARITY


def distance_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle distance in metres between two (lat, lon) points.

    Args:
        a: First point.
        b: Second point.
    """
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


class DocumentPipeline:
    """Upsert the page as a pending Document; suggest the office type of service pages."""

    def __init__(self, classifier: OfficeTypeClassifier) -> None:
        self._classifier = classifier

    @transaction.atomic
    def process(
        self, source: CrawlSource, page: ParsedPage, *, url: str, fetched_at: datetime
    ) -> None:
        """Create or update the Document for ``url``.

        Changed text sends an approved document back to review and drops its chunks.

        Args:
            source: The crawl source.
            page: The parsed page.
            url: The page's final URL (the Document key).
            fetched_at: When it was fetched.
        """
        text_hash = hashlib.sha256(page.text.encode()).hexdigest()
        document, created = Document.objects.get_or_create(
            url=url,
            defaults={"fetched_at": fetched_at, "text_hash": text_hash, "text": page.text},
        )
        if not created and document.text_hash != text_hash:
            document.chunks.all().delete()
            document.status = ReviewStatus.PENDING
        document.source = source
        document.kind = source.document_kind
        document.title = page.title or source.name
        document.publisher = source.publisher
        document.language = detect_language(page.text)
        document.section_label = page.section_label
        document.published_at = page.published_at
        document.fetched_at = fetched_at
        document.text, document.text_hash = page.text, text_hash
        document.corpus_version = settings.CORPUS_VERSION
        document.save()
        if document.kind == DocumentKind.SERVICE_PAGE:
            self._suggest_office_type(document, page.text)

    def _suggest_office_type(self, document: Document, text: str) -> None:
        """Store the classifier's suggestion as an unconfirmed ServiceOffice."""
        types = {office_type.code: office_type for office_type in OfficeType.objects.all()}
        try:
            code = self._classifier.classify(text, list(types))
        except Exception:
            # The suggestion is optional (the admin confirms or sets it), so a Gemini outage
            # must not block storing the document. Logged with the traceback.
            logger.warning(
                "Office type suggestion failed", exc_info=True, extra={"url": document.url}
            )
            return
        if code is not None:
            ServiceOffice.objects.get_or_create(document=document, office_type=types[code])


class OfficePipeline:
    """Store the offices of a directory page pending review.

    Structured offices from the site parser are used as they are; only pages without
    structure go to the (Gemini) extractor. Offices outside the source's name pattern or
    regions, or whose region or district cannot be matched unambiguously, are skipped and
    logged, never guessed.
    """

    def __init__(self, extractor: OfficeExtractor) -> None:
        self._extractor = extractor

    def _candidates(self, page: ParsedPage) -> list[OfficeCandidate]:
        """The page's structured offices, else what the extractor finds in its text."""
        if page.offices is not None:
            return list(page.offices)
        return self._extractor.extract(page.text)

    @staticmethod
    def _is_duplicate(
        office_type: OfficeType, candidate: OfficeCandidate, district_id: int
    ) -> bool:
        """Same type and district, and the same address, a near-identical name, or the same spot."""
        address = canonicalize(candidate.address)
        point = (
            (candidate.latitude, candidate.longitude)
            if candidate.latitude is not None and candidate.longitude is not None
            else None
        )
        for office in Office.objects.filter(office_type=office_type, district_id=district_id):
            if address == canonicalize(office.address) or same_name(candidate.name, office.name):
                return True
            if (
                point is not None
                and office.latitude is not None
                and office.longitude is not None
                and distance_m(point, (office.latitude, office.longitude))
                <= OFFICE_DUPLICATE_METRES
            ):
                return True
        return False

    @transaction.atomic
    def process(
        self, source: CrawlSource, page: ParsedPage, *, url: str, fetched_at: datetime
    ) -> None:
        """Create pending offices for every in-scope, matchable, new candidate on the page.

        Args:
            source: An office source (``office_type`` is required by its model).
            page: The parsed page.
            url: The page URL (stored as ``source_url``).
            fetched_at: When it was fetched (``data_as_of`` unless the page states a date).

        Raises:
            ValueError: When the source has no office type.
        """
        office_type = source.office_type
        if office_type is None:
            msg = f"Office source {source.id} has no office_type."
            raise ValueError(msg)
        name_pattern = re.compile(source.office_name_pattern, re.IGNORECASE)
        scope = list(source.office_regions.all())
        for candidate in self._candidates(page):
            if not name_pattern.search(candidate.name):
                logger.info("Office skipped: name pattern", extra={"office": candidate.name})
                continue
            place = _resolve_place(candidate, scope)
            if place is None:
                logger.warning(
                    "Office skipped: place not matched", extra={"office": candidate.name}
                )
                continue
            region, match = place
            if self._is_duplicate(office_type, candidate, match.district.id):
                continue
            listed = candidate if isinstance(candidate, ListedOffice) else None
            Office.objects.create(
                needs_review=match.needs_review,
                office_type=office_type,
                name=candidate.name,
                address=candidate.address,
                district=match.district,
                region=region,
                phone=candidate.phone,
                working_hours=[h.model_dump(by_alias=True) for h in candidate.working_hours],
                latitude=candidate.latitude,
                longitude=candidate.longitude,
                source=source,
                source_url=url,
                data_as_of=(listed.data_as_of if listed else None) or fetched_at.date(),
            )
