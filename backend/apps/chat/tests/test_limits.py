"""Tests for QuotaService (cache-backed counters and locks)."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.core.cache import cache
from django.test import override_settings

from apps.chat.limits import QuotaService
from apps.common.problems import QuotaExceeded, RateLimited, StreamInProgress

TASHKENT = ZoneInfo("Asia/Tashkent")
NOW = datetime(2026, 10, 22, 14, 45, 30, tzinfo=TASHKENT)


@pytest.fixture
def quota() -> QuotaService:
    """A quota service with a frozen clock."""
    return QuotaService(cache, clock=lambda: NOW)


async def test_counts_questions(quota: QuotaService) -> None:
    """Each consume adds one to hour and day counters."""
    await quota.aconsume("u1")
    await quota.aconsume("u1")
    usage = await quota.ausage("u1")
    assert (usage.hour_used, usage.day_used) == (2, 2)
    assert quota.usage("u1") == usage


@override_settings(CHAT_LIMIT_HOUR=1)
async def test_hourly_limit(quota: QuotaService) -> None:
    """Over the hourly limit: rate_limited with seconds to the next hour."""
    await quota.aconsume("u1")
    with pytest.raises(RateLimited) as caught:
        await quota.acheck("u1")
    assert caught.value.retry_after == 14 * 60 + 30 + 1


@override_settings(CHAT_LIMIT_DAY=1)
async def test_daily_limit(quota: QuotaService) -> None:
    """Over the daily limit: quota_exceeded until local midnight."""
    await quota.aconsume("u1")
    with pytest.raises(QuotaExceeded) as caught:
        await quota.acheck("u1")
    assert caught.value.retry_after == 9 * 3600 + 14 * 60 + 30 + 1
    assert caught.value.extensions() == {"scope": "user"}


@override_settings(GLOBAL_DAILY_TOKEN_CAP=100)
async def test_global_token_cap(quota: QuotaService) -> None:
    """The global token cap blocks everyone."""
    await quota.aadd_tokens(60)
    await quota.aadd_tokens(0)
    await quota.acheck("u1")
    await quota.aadd_tokens(40)
    assert await quota.atokens_today() == 100
    assert quota.tokens_today() == 100
    with pytest.raises(QuotaExceeded) as caught:
        await quota.acheck("u1")
    assert caught.value.extensions() == {"scope": "global"}


async def test_stream_lock(quota: QuotaService) -> None:
    """Only one stream per user until released."""
    await quota.aacquire_stream("u1")
    with pytest.raises(StreamInProgress):
        await quota.aacquire_stream("u1")
    await quota.aacquire_stream("u2")
    await quota.arelease_stream("u1")
    await quota.aacquire_stream("u1")
