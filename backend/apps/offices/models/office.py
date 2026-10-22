from django.core.exceptions import ValidationError
from django.db import models
from pydantic import ValidationError as SchemaError

from apps.common.constants import ReviewStatus
from apps.common.models import BaseModel
from apps.offices.hours import validate_working_hours
from apps.offices.models.office_type import OfficeType


class Office(BaseModel):
    """One physical office. Data comes only from reviewed sources, never the LLM."""

    office_type = models.ForeignKey(OfficeType, on_delete=models.PROTECT, related_name="offices")
    name = models.CharField(max_length=300)
    address = models.CharField(max_length=500)
    district = models.ForeignKey("geo.District", on_delete=models.PROTECT, related_name="offices")
    region = models.ForeignKey("geo.Region", on_delete=models.PROTECT, related_name="offices")
    phone = models.CharField(max_length=60, null=True, blank=True)  # noqa: DJ001
    working_hours = models.JSONField(default=list, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    source = models.ForeignKey(
        "collector.CrawlSource", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    source_url = models.URLField(max_length=1000)
    data_as_of = models.DateField()
    status = models.CharField(max_length=10, choices=ReviewStatus, default=ReviewStatus.PENDING)
    is_active = models.BooleanField(default=True)
    needs_review = models.BooleanField(
        default=False, help_text="District matched by fuzzy name only: check it before approving."
    )

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["office_type", "district", "status"])]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        """Working hours must follow contract §5 (the admin form enforces this).

        Raises:
            ValidationError: On malformed working hours.
        """
        try:
            self.working_hours = validate_working_hours(self.working_hours)
        except SchemaError as exc:
            raise ValidationError({"working_hours": str(exc)}) from exc
