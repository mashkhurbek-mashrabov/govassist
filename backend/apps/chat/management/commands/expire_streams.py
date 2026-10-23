from typing import Any

from django.core.management.base import BaseCommand

from apps.chat.services import expire_stale_streams


class Command(BaseCommand):
    """Mark answers stuck in ``streaming`` (older than the stream lock TTL) as failed."""

    help = "Mark dead streaming answers as failed (error_code=stopped)."

    def handle(self, *args: Any, **options: Any) -> None:
        """Expire every stale streaming answer and report how many.

        Args:
            *args: Unused.
            **options: Unused.
        """
        count = expire_stale_streams()
        self.stdout.write(self.style.SUCCESS(f"Expired {count} stale streaming answer(s)."))
