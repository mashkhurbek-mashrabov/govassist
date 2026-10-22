from django.db import models

from apps.common.models import BaseModel
from apps.offices.models.office_type import OfficeType


class ServiceOffice(BaseModel):
    """Which office type handles the service described by a service page."""

    document = models.ForeignKey(
        "corpus.Document", on_delete=models.CASCADE, related_name="service_offices"
    )
    office_type = models.ForeignKey(OfficeType, on_delete=models.CASCADE, related_name="+")
    confirmed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["document", "office_type"], name="uniq_service_office"),
        ]

    def __str__(self) -> str:
        return f"{self.document_id} → {self.office_type_id}"
