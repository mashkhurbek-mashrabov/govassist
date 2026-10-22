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
