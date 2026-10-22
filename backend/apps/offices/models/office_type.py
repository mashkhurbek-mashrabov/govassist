from django.db import models

from apps.common.models import BaseModel, LocalizedName


class OfficeType(BaseModel, LocalizedName):
    """A kind of office, e.g. ``public_service_center``. Names are the labels."""

    code = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code
