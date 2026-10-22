"""Pipelines for processing crawled pages into documents and offices."""

import hashlib
import logging
import re
from collections.abc import Callable
from datetime import datetime
from typing import Any, Protocol

from django.conf import settings

from apps.collector.extraction import (
    OfficeCandidate,
    OfficeExtractor,
    OfficeTypeClassifier,
)
from apps.collector.fetchers import FetchResult
from apps.collector.models import CrawlSource
from apps.collector.parsers import parse
from apps.common.models import ReviewStatus
from apps.common.text import canonicalize, detect_language, detect_script, uz_cyrl_to_latn
from apps.corpus.models import Document, DocumentKind
from apps.geo.models import Region
from apps.offices.hours import clean_working_hours
from apps.offices.matching import DistrictMatch, match_district
from apps.offices.models import Office, OfficeType, ServiceOffice

logger = logging.getLogger(__name__)

REGION_SUFFIXES = (
    "viloyati",
    "viloyat",
    "shahri",
    "shahar",
    "respublikasi",
    "respublika",
    "область",
    "город",
    "республика",
    "region",
    "city",
    "republic",
)
_REGION_SUFFIX_RE = re.compile(
    r"\s+(?:"
    + "|".join(re.escape(s) for s in sorted(REGION_SUFFIXES, key=len, reverse=True))
    + r")$",
    re.IGNORECASE,
)


def _normalize_region_name(name: str) -> str:
    """Normalize a region name by transliterating Cyrillic and stripping suffixes."""
    if detect_script(name) == "cyrl":
        name = uz_cyrl_to_latn(name)
    canon = canonicalize(name)
    return _REGION_SUFFIX_RE.sub("", canon).strip()


def find_region(name: str) -> Region | None:
    """Match a region name to an existing Region record by any localized name field.

    Args:
        name: Extracted region name string.

    Returns:
        Region instance if matched, else None.
    """
    if not name or not name.strip():
        return None
    normalized_target = _normalize_region_name(name)
    if not normalized_target:
        return None

    for reg in Region.objects.all():
        for field_name in ("name_uz_latn", "name_uz_cyrl", "name_ru", "name_en"):
            val: str = getattr(reg, field_name, "")
            if not val:
                continue
            if normalized_target == _normalize_region_name(val):
                return reg
    return None


class Pipeline(Protocol):
    """Protocol for processing crawled pages into corpus documents or office records."""

    def process(
        self,
        source: CrawlSource,
        page: FetchResult,
        *,
        url: str,
        fetched_at: datetime,
    ) -> None:
        """Process one crawled page.

        Args:
            source: Source configuration for the crawl.
            page: Raw fetched result.
            url: Page URL.
            fetched_at: Timestamp when page was fetched.
        """
        ...


class DocumentPipeline:
    """Processes crawled pages into Document rows and classifies service office associations."""

    def __init__(
        self,
        classifier: OfficeTypeClassifier | None = None,
    ) -> None:
        """Initialize pipeline with optional office type classifier.

        Args:
            classifier: Classifier to identify service center types for service pages.
        """
        self.classifier = classifier

    def process(
        self,
        source: CrawlSource,
        page: FetchResult,
        *,
        url: str,
        fetched_at: datetime,
    ) -> None:
        """Upsert Document and optionally link to ServiceOffice.

        Args:
            source: CrawlSource configuration.
            page: Fetched page data.
            url: Canonical URL.
            fetched_at: Fetch timestamp.
        """
        parsed = parse(page, source)
        text_hash = hashlib.sha256(parsed.text.encode("utf-8")).hexdigest()
        detected_lang = detect_language(parsed.text)
        corpus_version = getattr(settings, "CORPUS_VERSION", "2026.10")

        doc = Document.objects.filter(url=url).first()
        if doc is None:
            doc = Document.objects.create(
                source=source,
                kind=source.document_kind,
                title=parsed.title or "Hujjat",
                url=url,
                publisher=source.publisher,
                language=detected_lang,
                section_label=parsed.section_label,
                published_at=parsed.published_at,
                fetched_at=fetched_at,
                text=parsed.text,
                text_hash=text_hash,
                corpus_version=corpus_version,
                status=ReviewStatus.PENDING,
                is_active=True,
            )
        else:
            if doc.text_hash != text_hash:
                doc.chunks.all().delete()
                doc.status = ReviewStatus.PENDING
                doc.text = parsed.text
                doc.text_hash = text_hash

            doc.source = source
            doc.kind = source.document_kind
            doc.title = parsed.title or doc.title
            doc.publisher = source.publisher
            doc.language = detected_lang
            doc.section_label = parsed.section_label or doc.section_label
            doc.published_at = parsed.published_at or doc.published_at
            doc.fetched_at = fetched_at
            doc.corpus_version = corpus_version
            doc.save()

        # Classify service page office type if applicable
        if source.document_kind == DocumentKind.SERVICE_PAGE and self.classifier is not None:
            office_types = {ot.code: ot for ot in OfficeType.objects.all()}
            if office_types:
                matched_code = self.classifier.classify(parsed.text, list(office_types.keys()))
                if matched_code and matched_code in office_types:
                    ServiceOffice.objects.get_or_create(
                        document=doc,
                        office_type=office_types[matched_code],
                        defaults={"confirmed": False},
                    )


class OfficePipeline:
    """Processes crawled directory pages into physical Office records."""

    def __init__(
        self,
        extractor: OfficeExtractor,
        hours_cleaner: Callable[[list[Any]], list[dict[str, Any]]] = clean_working_hours,
        matcher: Callable[[str, Region], DistrictMatch | None] = match_district,
        region_finder: Callable[[str], Region | None] = find_region,
    ) -> None:
        """Initialize OfficePipeline with extraction, hours cleaning, and matching tools.

        Args:
            extractor: Structured office candidate extractor.
            hours_cleaner: Working hours validator/cleaner.
            matcher: District matcher function.
            region_finder: Region lookup helper.
        """
        self.extractor = extractor
        self.hours_cleaner = hours_cleaner
        self.matcher = matcher
        self.region_finder = region_finder

    def process(
        self,
        source: CrawlSource,
        page: FetchResult,
        *,
        url: str,
        fetched_at: datetime,
    ) -> None:
        """Extract and upsert physical office records from page.

        Args:
            source: Source with mandatory office_type configured.
            page: Fetched page result.
            url: Page URL.
            fetched_at: Fetch timestamp.
        """
        if source.office_type is None:
            logger.error("Source %s has no office_type configured.", source.name)
            return

        parsed = parse(page, source)
        candidates: list[OfficeCandidate] = self.extractor.extract(parsed.text)

        for candidate in candidates:
            region = self.region_finder(candidate.region_name)
            if region is None:
                logger.warning(
                    "Region not matched for candidate '%s': %s",
                    candidate.name,
                    candidate.region_name,
                )
                continue

            match = self.matcher(candidate.district_name, region)
            if match is None:
                logger.warning(
                    "District not matched in %s for '%s': %s",
                    region.name_uz_latn,
                    candidate.name,
                    candidate.district_name,
                )
                continue

            cleaned_hours = self.hours_cleaner(
                [h.model_dump(by_alias=True) for h in candidate.working_hours]
            )

            # Deduplicate by (office_type, district, canonicalize(address))
            canon_address = canonicalize(candidate.address)
            existing_offices = Office.objects.filter(
                office_type=source.office_type,
                district=match.district,
            )
            if any(canonicalize(o.address) == canon_address for o in existing_offices):
                logger.info(
                    "Duplicate office skipped: %s in %s",
                    candidate.name,
                    match.district.name_uz_latn,
                )
                continue

            Office.objects.create(
                office_type=source.office_type,
                name=candidate.name,
                address=candidate.address,
                district=match.district,
                region=region,
                phone=candidate.phone,
                working_hours=cleaned_hours,
                latitude=candidate.latitude,
                longitude=candidate.longitude,
                source=source,
                source_url=url,
                data_as_of=fetched_at.date(),
                status=ReviewStatus.PENDING,
                is_active=True,
            )
