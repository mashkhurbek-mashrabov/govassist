"""drf-spectacular extensions (imported in ``CommonConfig.ready``)."""

from drf_spectacular.authentication import SessionScheme


class CsrfProblemSessionScheme(SessionScheme):  # type: ignore[no-untyped-call]
    """Document ``CsrfProblemSessionAuthentication`` as the standard session cookie."""

    target_class = "apps.common.authentication.CsrfProblemSessionAuthentication"
