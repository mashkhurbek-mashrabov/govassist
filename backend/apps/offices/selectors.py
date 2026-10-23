from typing import Any

from apps.offices.models import OfficeType


async def aoffice_type_label(office: dict[str, Any] | None, language: str) -> str | None:
    """The matched office type's label in ``language`` (the prompt's «label»), or None.

    The office card itself keeps the user's ``ui_language``; the prompt names the office in the
    question's language.

    Args:
        office: The ``OfficeMatch``, if any.
        language: The question's language.
    """
    if office is None:
        return None
    office_type = await OfficeType.objects.filter(code=office["office_type"]["code"]).afirst()
    if office_type is None:
        return str(office["office_type"]["label"])
    return office_type.name_for(language)
