"""Working hours schema and cleaning per contract §5."""

import logging
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

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


WORKING_HOURS_LIST = TypeAdapter(list[WorkingHours])


def validate_working_hours(raw: Any) -> list[dict[str, Any]]:
    """Validate a whole ``working_hours`` value (contract §5) and return it normalized.

    Args:
        raw: The stored JSON value.

    Raises:
        ValidationError: When any entry is malformed.
    """
    return [item.model_dump(by_alias=True) for item in WORKING_HOURS_LIST.validate_python(raw)]
