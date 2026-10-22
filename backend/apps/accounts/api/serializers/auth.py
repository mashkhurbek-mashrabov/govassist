from typing import Any

from rest_framework import serializers


class ResendVerificationSerializer(serializers.Serializer[Any]):
    """POST ``/auth/resend-verification`` body."""

    email = serializers.EmailField()
