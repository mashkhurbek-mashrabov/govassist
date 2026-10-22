"""Curated starter questions per UI language (questions only, no facts)."""

from apps.chat.constants import MAX_SUGGESTIONS, SUGGESTIONS
from apps.common.constants import Lang


def suggestions_for(lang: str) -> list[dict[str, str]]:
    """At most six starter questions in ``lang``.

    Args:
        lang: A ``Lang`` value.
    """
    items = SUGGESTIONS.get(lang, SUGGESTIONS[Lang.UZ_LATN])[:MAX_SUGGESTIONS]
    return [{"text": text, "category": category} for text, category in items]
