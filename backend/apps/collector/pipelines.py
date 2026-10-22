"""What a parsed page becomes: a pending Document, or pending Offices (plan §5 step 3)."""

import hashlib
import logging
from datetime import datetime
from typing import Protocol

from django.conf import settings
from django.db import transaction

from apps.collector.constants import REGION_WORDS
from apps.collector.extraction import (
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
from apps.geo.constants import NAME_FIELDS
from apps.geo.models import Region
from apps.offices.matching import match_district
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
    latin = uz_cyrl_to_latn(name) if detect_script(name) == "cyrl" else name
    return " ".join(REGION_WORDS.sub(" ", canonicalize(latin)).split())


def find_region(name: str) -> Region | None:
    """The region whose name (any language) matches ``name`` exactly after normalization.

    Args:
        name: Region name as written on the page.
    """
    key = _region_key(name)
    if not key:
        return None
    return next(
        (
            region
            for region in Region.objects.all()
            if any(_region_key(getattr(region, field)) == key for field in NAME_FIELDS)
        ),
        None,
    )


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
    """Extract offices from a directory page and store them pending review.

    Offices whose region or district cannot be matched are skipped and logged, never guessed.
    """

    def __init__(self, extractor: OfficeExtractor) -> None:
        self._extractor = extractor

    def _is_duplicate(
        self, office_type: OfficeType, candidate: OfficeCandidate, district_id: int
    ) -> bool:
        """Same type, district and canonical address already stored."""
        address = canonicalize(candidate.address)
        existing = Office.objects.filter(office_type=office_type, district_id=district_id)
        return any(canonicalize(office.address) == address for office in existing)

    @transaction.atomic
    def process(
        self, source: CrawlSource, page: ParsedPage, *, url: str, fetched_at: datetime
    ) -> None:
        """Create pending offices for every matchable candidate on the page.

        Args:
            source: An office source (``office_type`` is required by its model).
            page: The parsed page.
            url: The page URL (stored as ``source_url``).
            fetched_at: When it was fetched (``data_as_of``).

        Raises:
            ValueError: When the source has no office type.
        """
        office_type = source.office_type
        if office_type is None:
            msg = f"Office source {source.id} has no office_type."
            raise ValueError(msg)
        for candidate in self._extractor.extract(page.text):
            region = find_region(candidate.region_name)
            match = match_district(candidate.district_name, region) if region else None
            if region is None or match is None:
                logger.warning(
                    "Office skipped: place not matched", extra={"office": candidate.name}
                )
                continue
            if match.needs_review:
                logger.info("Fuzzy district match", extra={"office": candidate.name})
            if self._is_duplicate(office_type, candidate, match.district.id):
                continue
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
                data_as_of=fetched_at.date(),
            )
