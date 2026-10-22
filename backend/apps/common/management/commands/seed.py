from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.collector.seeding import seed_sample_sources
from apps.geo.services import seed_geo
from apps.offices.seeding import seed_office_types


class Command(BaseCommand):
    """Load SOATO geo data, office types and the sample crawl sources (idempotent)."""

    help = "Seed geo, office types and sample sources."

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        """Run every seed step and report counts.

        Args:
            *args: Unused.
            **options: Unused.
        """
        regions, districts = seed_geo()
        office_types = seed_office_types()
        sources = seed_sample_sources()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {regions} regions, {districts} districts, {office_types} office types, "
                f"{sources} sample sources."
            )
        )
