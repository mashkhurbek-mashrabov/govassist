from django.apps import AppConfig


class CommonConfig(AppConfig):
    """Shared building blocks: base model, admin, problems, text, PII, Gemini."""

    name = "apps.common"
