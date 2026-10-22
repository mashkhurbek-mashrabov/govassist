"""Tests for Turnstile verification (HTTP mocked, no network)."""

from unittest.mock import MagicMock, patch

import httpx

from apps.accounts.turnstile import verify_turnstile


def _reply(payload: dict[str, object]) -> MagicMock:
    """Build a fake httpx response with ``payload`` as JSON."""
    response = MagicMock()
    response.json.return_value = payload
    return response


def test_success() -> None:
    """Cloudflare says success: token accepted, IP forwarded."""
    with patch(
        "apps.accounts.turnstile.httpx.post", return_value=_reply({"success": True})
    ) as post:
        assert verify_turnstile("tok", "1.2.3.4") is True
    assert post.call_args.kwargs["data"]["remoteip"] == "1.2.3.4"


def test_rejected() -> None:
    """Cloudflare says no: token refused."""
    with patch("apps.accounts.turnstile.httpx.post", return_value=_reply({"success": False})):
        assert verify_turnstile("tok") is False


def test_network_error_fails_closed() -> None:
    """A network error never lets a signup through."""
    with patch("apps.accounts.turnstile.httpx.post", side_effect=httpx.ConnectError("down")):
        assert verify_turnstile("tok") is False
