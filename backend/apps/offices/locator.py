"""Find the office for a retrieved service in the user's district (plan §10, contract §5)."""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from apps.common.constants import ReviewStatus
from apps.corpus.constants import DocumentKind
from apps.offices.maps import map_url
from apps.offices.models import Office, OfficeType, ServiceOffice
from apps.offices.schemas import OfficeMatch, OfficeOut, OfficeTypeRef, PlaceRef


def _type_ref(office_type: OfficeType, lang: str) -> OfficeTypeRef:
    """``{code, label}`` with the label in ``lang``."""
    return OfficeTypeRef(code=office_type.code, label=office_type.name_for(lang))


def office_out(office: Office, lang: str) -> OfficeOut:
    """Build the contract's ``Office`` object.

    Args:
        office: An office with ``office_type``, ``district`` and ``region`` loaded.
        lang: Language for labels and place names.
    """
    return OfficeOut.model_validate(
        {
            "id": str(office.id),
            "name": office.name,
            "office_type": _type_ref(office.office_type, lang),
            "address": office.address,
            "district": PlaceRef(id=office.district_id, name=office.district.name_for(lang)),
            "region": PlaceRef(id=office.region_id, name=office.region.name_for(lang)),
            "phone": office.phone,
            "working_hours": office.working_hours,
            "latitude": office.latitude,
            "longitude": office.longitude,
            "map_url": map_url(office.name, office.address, office.latitude, office.longitude),
            "data_as_of": office.data_as_of.isoformat(),
            "source_url": office.source_url,
        }
    )


def _first_office_type(document_ids: Sequence[UUID]) -> OfficeType | None:
    """Office type of the best-ranked service page that has a confirmed mapping.

    Args:
        document_ids: Retrieved document ids, best first.
    """
    mappings = ServiceOffice.objects.filter(
        document_id__in=document_ids, confirmed=True, document__kind=DocumentKind.SERVICE_PAGE
    ).select_related("office_type")
    by_document = {mapping.document_id: mapping.office_type for mapping in mappings}
    return next((by_document[d] for d in document_ids if d in by_document), None)


def _find_office(office_type: OfficeType, **place: int | None) -> Office | None:
    """First approved, active office of ``office_type`` in a district or region.

    Args:
        office_type: The office type.
        **place: ``district_id=…`` or ``region_id=…``.
    """
    return (
        Office.objects.filter(
            office_type=office_type, status=ReviewStatus.APPROVED, is_active=True, **place
        )
        .select_related("office_type", "district", "region")
        .order_by("name")
        .first()
    )


def locate(
    document_ids: Sequence[UUID], *, district_id: int | None, region_id: int | None, lang: str
) -> dict[str, Any] | None:
    """Return the ``OfficeMatch`` for the retrieved documents, or None.

    District first, then region, else ``match: "none"``. None means no retrieved service
    maps to an office type, so no ``office`` event is sent.

    Args:
        document_ids: Retrieved document ids, best first.
        district_id: The user's district.
        region_id: The user's region.
        lang: Language for labels.
    """
    office_type = _first_office_type(document_ids)
    if office_type is None:
        return None
    office = _find_office(office_type, district_id=district_id) if district_id else None
    level = "district" if office else "none"
    if office is None and region_id:
        office = _find_office(office_type, region_id=region_id)
        level = "region" if office else "none"
    result = OfficeMatch.model_validate(
        {
            "match": level,
            "office_type": _type_ref(office_type, lang),
            "office": office_out(office, lang) if office else None,
        }
    )
    return result.model_dump(mode="json", by_alias=True)
