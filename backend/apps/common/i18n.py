"""UI/content languages and request language resolution (contract §1)."""

from django.http import HttpRequest

from apps.common.constants import ACCEPT_LANGUAGE_PREFIXES, DEFAULT_LANG, Lang


def parse_lang(value: str | None) -> Lang | None:
    """Return the ``Lang`` for an exact code, or None when unsupported.

    Args:
        value: A code such as ``uz-Latn``.

    Returns:
        The matching language or None.
    """
    return Lang(value) if value in Lang.values else None


def _from_accept_language(header: str) -> Lang | None:
    """Pick the first supported language from an Accept-Language header.

    Args:
        header: Raw header value.

    Returns:
        The first supported language or None.
    """
    for part in header.split(","):
        tag = part.split(";")[0].strip().lower()
        for prefix, lang in ACCEPT_LANGUAGE_PREFIXES:
            if tag.startswith(prefix):
                return lang
    return None


def resolve_lang(request: HttpRequest) -> Lang:
    """Resolve the language: ``?lang=``, user's ``ui_language``, Accept-Language, default.

    Args:
        request: The current request.

    Returns:
        The language to localize names in.
    """
    explicit = parse_lang(request.GET.get("lang"))
    if explicit:
        return explicit
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return Lang(user.ui_language)
    return _from_accept_language(request.headers.get("Accept-Language", "")) or DEFAULT_LANG
