from typing import Any

from rest_framework import serializers

from apps.accounts.constants import DISPLAY_NAME_MAX_LENGTH
from apps.accounts.models import User
from apps.accounts.services import ProfileUpdate
from apps.common.constants import Lang
from apps.geo.api.serializers import PlaceSerializer
from apps.geo.models import District, Region


class QuotaSerializer(serializers.Serializer[Any]):
    """Hourly and daily question usage."""

    hour_limit = serializers.IntegerField()
    hour_used = serializers.IntegerField()
    day_limit = serializers.IntegerField()
    day_used = serializers.IntegerField()


class MeSerializer(serializers.Serializer[User]):
    """The ``Me`` object of the contract.

    Context: ``lang``, ``email_verified`` and ``quota`` are computed by the view.
    """

    id = serializers.UUIDField()
    email = serializers.EmailField()
    email_verified = serializers.SerializerMethodField()
    has_password = serializers.SerializerMethodField()
    display_name = serializers.CharField(allow_null=True)
    ui_language = serializers.ChoiceField(choices=Lang.choices)
    region = PlaceSerializer(allow_null=True)
    district = PlaceSerializer(allow_null=True)
    profile_complete = serializers.BooleanField()
    quota = serializers.SerializerMethodField()

    def get_email_verified(self, obj: User) -> bool:
        """Return the verification flag computed by the view.

        Args:
            obj: The user.
        """
        return bool(self.context["email_verified"])

    def get_has_password(self, obj: User) -> bool:
        """False for Google-only accounts that never set a password.

        Args:
            obj: The user.
        """
        return obj.has_usable_password()

    def get_quota(self, obj: User) -> dict[str, int]:
        """Return the quota usage computed by the view.

        Args:
            obj: The user.
        """
        return QuotaSerializer(self.context["quota"]).data


class MeUpdateSerializer(serializers.Serializer[Any]):
    """PATCH ``/me`` body: all fields optional; ``district_id`` must be in ``region_id``.

    Changing ``region_id`` needs a ``district_id`` in the new region (contract v1.4).
    """

    ui_language = serializers.ChoiceField(choices=Lang.choices, required=False)
    region_id = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(), required=False, source="region"
    )
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(), required=False, source="district"
    )
    display_name = serializers.CharField(
        max_length=DISPLAY_NAME_MAX_LENGTH, required=False, allow_null=True, allow_blank=True
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Check that the district belongs to the region (given or current).

        Args:
            attrs: Field-validated data.

        Returns:
            The same data.

        Raises:
            serializers.ValidationError: On a district outside the region.
        """
        district: District | None = attrs.get("district")
        user: User = self.context["user"]
        region_id = attrs["region"].id if "region" in attrs else user.region_id
        if district is not None and region_id is not None and district.region_id != region_id:
            raise serializers.ValidationError(
                {"district_id": ["District does not belong to the region."]}
            )
        region_changed = "region" in attrs and attrs["region"].id != user.region_id
        if region_changed and district is None and user.district_id is not None:
            raise serializers.ValidationError(
                {"district_id": ["Choose a district in the new region."]}
            )
        return attrs

    def to_change(self) -> ProfileUpdate:
        """Convert validated data to a service command.

        Returns:
            The profile change.
        """
        data = self.validated_data
        return ProfileUpdate(
            ui_language=data.get("ui_language"),
            region=data.get("region"),
            district=data.get("district"),
            display_name=data.get("display_name"),
            display_name_set="display_name" in data,
        )


class ResendVerificationSerializer(serializers.Serializer[Any]):
    """POST ``/auth/resend-verification`` body."""

    email = serializers.EmailField()


class DeleteMeSerializer(serializers.Serializer[Any]):
    """DELETE ``/me`` body: ``{"confirm": true}`` is required."""

    confirm = serializers.BooleanField()

    def validate_confirm(self, value: bool) -> bool:
        """Require an explicit ``true``.

        Args:
            value: The submitted flag.

        Raises:
            serializers.ValidationError: When not true.
        """
        if not value:
            msg = "Set confirm to true to delete the account."
            raise serializers.ValidationError(msg)
        return value
