"""Cloudflare Turnstile server-side verification."""

import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


def verify_turnstile(token: str, remote_ip: str | None = None) -> bool:
    """Ask Cloudflare whether a Turnstile token is valid.

    Args:
        token: The token the widget produced in the browser.
        remote_ip: Optional client IP, sent to Cloudflare as extra signal.

    Returns:
        True only when Cloudflare confirms the token. Network errors count as failure.
    """
    payload = {"secret": settings.TURNSTILE_SECRET_KEY, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip
    try:
        response = httpx.post(
            settings.TURNSTILE_VERIFY_URL, data=payload, timeout=settings.TURNSTILE_TIMEOUT_S
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.warning("Turnstile verification request failed", exc_info=True)
        return False
    return bool(response.json().get("success"))
