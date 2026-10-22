from django.db import models

from apps.common.models import LocalizedName


class Region(LocalizedName):
    """A region (viloyat), the Republic of Karakalpakstan or Tashkent city.

    The primary key is the official SOATO code, so it never changes.
    """

    id = models.PositiveIntegerField(primary_key=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name_uz_latn


class District(LocalizedName):
    """A district (tuman) or district-level city inside a region."""

    class Kind(models.TextChoices):
        """Administrative kind of the unit."""

        DISTRICT = "district", "District"
        CITY = "city", "City"

    id = models.PositiveIntegerField(primary_key=True)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="districts")
    kind = models.CharField(max_length=10, choices=Kind, default=Kind.DISTRICT)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name_uz_latn
