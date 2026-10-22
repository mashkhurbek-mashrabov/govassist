"""Contract §5 office objects (``OfficeMatch``, ``Office``), used for payloads and OpenAPI."""

from typing import Literal

from pydantic import BaseModel

from apps.offices.hours import WorkingHours


class OfficeTypeRef(BaseModel):
    """``{code, label}`` of an office type."""

    code: str
    label: str


class PlaceRef(BaseModel):
    """``{id, name}`` of a region or district."""

    id: int
    name: str


class OfficeOut(BaseModel):
    """One office as shown on the office card."""

    id: str
    name: str
    office_type: OfficeTypeRef
    address: str
    district: PlaceRef
    region: PlaceRef
    phone: str | None
    working_hours: list[WorkingHours]
    latitude: float | None
    longitude: float | None
    map_url: str
    data_as_of: str
    source_url: str


class OfficeMatch(BaseModel):
    """Result of the district → region office lookup."""

    match: Literal["district", "region", "none"]
    office_type: OfficeTypeRef
    office: OfficeOut | None
