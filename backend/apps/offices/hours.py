"""Working hours schema and cleaning per contract §5."""

import logging
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from apps.offices.constants import TIME_REGEX

logger = logging.getLogger(__name__)

type Day = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class BreakTime(BaseModel):
    """Daily break window within working hours."""

    start: str = Field(pattern=TIME_REGEX, description="Break start in HH:MM format")
    end: str = Field(pattern=TIME_REGEX, description="Break end in HH:MM format")


class WorkingHours(BaseModel):
    """Working hours specification for an office matching contract §5."""

    model_config = ConfigDict(populate_by_name=True)

    days: list[Day]
    open: str = Field(pattern=TIME_REGEX, description="Opening time in HH:MM format")
    close: str = Field(pattern=TIME_REGEX, description="Closing time in HH:MM format")
    break_: BreakTime | None = Field(
        default=None,
        alias="break",
        description="Lunch or shift break window",
    )


def clean_working_hours(raw: list[Any]) -> list[dict[str, Any]]:
    """Validate and clean raw working hours entries.

    Drops invalid items after logging a warning. Never infers or invents
    missing fields.

    Args:
        raw: List of unstructured or extracted working hours objects/dicts.

    Returns:
        List of JSON-serializable dictionaries matching contract §5.
    """
    cleaned: list[dict[str, Any]] = []
    for item in raw:
        try:
            validated = WorkingHours.model_validate(item)
            cleaned.append(validated.model_dump(by_alias=True))
        except ValidationError as exc:
            logger.warning("Dropping invalid working hours entry: %s (%s)", item, exc)
    return cleaned
