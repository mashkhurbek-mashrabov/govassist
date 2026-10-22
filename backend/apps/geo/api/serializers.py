from typing import Any

from rest_framework import serializers

from apps.common.models import LocalizedName


class PlaceSerializer(serializers.Serializer[Any]):
    """``{id, name}`` with the name localized to ``context["lang"]`` (Region / District)."""

    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()

    def get_name(self, obj: LocalizedName) -> str:
        """Return the name in the request language.

        Args:
            obj: A region or district.
        """
        return obj.name_for(self.context["lang"])
