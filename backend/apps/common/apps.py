from django.apps import AppConfig


class CommonConfig(AppConfig):
    """Shared building blocks: base model, admin, problems, text, PII, Gemini."""

    name = "apps.common"

    def ready(self) -> None:
        """Register the OpenAPI extensions."""
        from apps.common import schema  # noqa: F401, PLC0415 (registration side effect)
