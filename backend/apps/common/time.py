from datetime import UTC, datetime


def isoformat_utc(value: datetime) -> str:
    """ISO 8601 in UTC with a ``Z`` suffix, the contract's timestamp format.

    Args:
        value: An aware datetime.
    """
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
