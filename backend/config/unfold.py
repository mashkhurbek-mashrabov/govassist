"""django-unfold callbacks and sidebar. Imported by settings, so no model imports at top."""

from typing import Any

from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse_lazy


def _item(title: str, icon: str, model: str) -> dict[str, Any]:
    """Build one sidebar link to a model changelist.

    Args:
        title: Link text.
        icon: Material Symbols icon name.
        model: ``app_label_modelname`` for the admin URL.
    """
    return {"title": title, "icon": icon, "link": reverse_lazy(f"admin:{model}_changelist")}


SIDEBAR_NAVIGATION: list[dict[str, Any]] = [
    {
        "title": "Knowledge",
        "items": [
            _item("Crawl sources", "travel_explore", "collector_crawlsource"),
            _item("Crawl jobs", "work_history", "collector_crawljob"),
            _item("Documents", "description", "corpus_document"),
            _item("Chunks", "segment", "corpus_chunk"),
        ],
    },
    {
        "title": "Offices",
        "items": [
            _item("Office types", "category", "offices_officetype"),
            _item("Offices", "apartment", "offices_office"),
            _item("Service → Office", "link", "offices_serviceoffice"),
        ],
    },
    {
        "title": "Users",
        "items": [
            _item("Users", "person", "accounts_user"),
            _item("Groups", "group", "auth_group"),
        ],
    },
    {
        "title": "Chat",
        "items": [
            _item("Conversations", "forum", "chat_conversation"),
            _item("Messages", "chat", "chat_message"),
            _item("Feedback", "thumbs_up_down", "chat_feedback"),
        ],
    },
]


def environment_callback(request: HttpRequest) -> list[str]:
    """Show a DEV/PROD badge in the admin header.

    Args:
        request: The admin request.

    Returns:
        ``[label, color]`` for Unfold.
    """
    name = settings.ENVIRONMENT_NAME
    return [name, "danger" if name == "PROD" else "info"]


def dashboard_callback(request: HttpRequest, context: dict[str, Any]) -> dict[str, Any]:
    """Add the knowledge/office/chat stats to the admin index page.

    Args:
        request: The admin request.
        context: The template context.

    Returns:
        The context with ``kpis``.
    """
    from apps.common.dashboard import dashboard_kpis  # noqa: PLC0415 (apps not ready at import)

    context["kpis"] = dashboard_kpis()
    return context
