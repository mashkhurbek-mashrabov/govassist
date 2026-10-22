from django.db import models

from apps.common.models import LocalizedName
from apps.geo.constants import DistrictKind
from apps.geo.models.region import Region


class District(LocalizedName):
    """A district (tuman) or district-level city inside a region."""

    Kind = DistrictKind

    id = models.PositiveIntegerField(primary_key=True)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="districts")
    kind = models.CharField(max_length=10, choices=Kind, default=Kind.DISTRICT)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name_uz_latn
