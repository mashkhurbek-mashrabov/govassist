from typing import Any

from django.core.management.base import BaseCommand

from apps.geo.services import seed_geo


class Command(BaseCommand):
    """Load regions and districts from the official SOATO fixture."""

    help = "Upsert SOATO regions and districts."

    def handle(self, *args: Any, **options: Any) -> None:
        """Run the seed and report counts.

        Args:
            *args: Unused.
            **options: Unused.
        """
        regions, districts = seed_geo()
        self.stdout.write(self.style.SUCCESS(f"Seeded {regions} regions, {districts} districts."))
