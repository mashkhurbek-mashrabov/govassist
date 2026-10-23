"""Tests for working hours validation and cleaning."""

from typing import Any

import pytest
from pydantic import ValidationError

from apps.offices.hours import BreakTime, WorkingHours

NAMUNA_WORKING_HOURS_DATA: dict[str, Any] = {
    "days": ["mon", "tue", "wed", "thu", "fri"],
    "open": "09:00",
    "close": "18:00",
    "break": {"start": "13:00", "end": "14:00"},
}

NAMUNA_HOURS_NO_BREAK_DATA: dict[str, Any] = {
    "days": ["sat"],
    "open": "09:00",
    "close": "15:00",
    "break": None,
}


def test_working_hours_valid() -> None:
    """Verifies that valid hours with break validate correctly."""
    hours = WorkingHours.model_validate(NAMUNA_WORKING_HOURS_DATA)
    assert hours.days == ["mon", "tue", "wed", "thu", "fri"]
    assert hours.open == "09:00"
    assert hours.close == "18:00"
    assert hours.break_ is not None
    assert hours.break_.start == "13:00"
    assert hours.break_.end == "14:00"

    dumped = hours.model_dump(by_alias=True)
    assert dumped["break"] == {"start": "13:00", "end": "14:00"}


def test_working_hours_without_break() -> None:
    """Verifies that hours without break validate and dump with break=None."""
    hours = WorkingHours.model_validate(NAMUNA_HOURS_NO_BREAK_DATA)
    assert hours.break_ is None
    dumped = hours.model_dump(by_alias=True)
    assert dumped["break"] is None


def test_working_hours_invalid_day() -> None:
    """Verifies that non-standard days fail validation."""
    data = {
        "days": ["monday"],  # invalid literal
        "open": "09:00",
        "close": "18:00",
    }
    with pytest.raises(ValidationError):
        WorkingHours.model_validate(data)


def test_working_hours_invalid_time_format() -> None:
    """Verifies that malformed time strings fail validation."""
    data = {
        "days": ["mon"],
        "open": "9:00",  # missing leading zero
        "close": "25:00",  # hour > 23
    }
    with pytest.raises(ValidationError):
        WorkingHours.model_validate(data)


def test_break_time_invalid_format() -> None:
    """Verifies BreakTime regex enforcement."""
    with pytest.raises(ValidationError):
        BreakTime(start="12:60", end="13:00")
