import uuid

from django.db import models

from apps.common.constants import Lang


class BaseModel(models.Model):
    """Abstract base for every model: time-ordered UUIDv7 key plus timestamps."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class LocalizedName(models.Model):
    """Abstract name in the four supported languages."""

    name_uz_latn = models.CharField(max_length=120)
    name_uz_cyrl = models.CharField(max_length=120)
    name_ru = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120)

    class Meta:
        abstract = True

    def name_for(self, lang: str) -> str:
        """Return the name in ``lang``, falling back to Uzbek Latin.

        Args:
            lang: A ``Lang`` value.

        Returns:
            The localized name.
        """
        names = {
            Lang.UZ_LATN: self.name_uz_latn,
            Lang.UZ_CYRL: self.name_uz_cyrl,
            Lang.RU: self.name_ru,
            Lang.EN: self.name_en,
        }
        return names.get(Lang(lang), "") or self.name_uz_latn
