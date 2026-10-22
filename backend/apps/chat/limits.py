"""Per-user question quotas, the global daily token cap and the one-stream lock.

Counters live in the Django cache (Redis in dev/prod). ``cache.add`` is an atomic
``SET NX EX``, which is what the stream lock needs.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.cache import BaseCache, cache
from django.utils import timezone

from apps.common.problems import QuotaExceeded, RateLimited, StreamInProgress

HOUR_TTL_S = 3600
DAY_TTL_S = 90_000


def local_now() -> datetime:
    """Current time in ``LOCAL_TIME_ZONE`` (Tashkent), where quota windows reset."""
    return timezone.localtime(timezone=ZoneInfo(settings.LOCAL_TIME_ZONE))


@dataclass(frozen=True)
class QuotaUsage:
    """Current question counts against the limits (``Me.quota`` in the contract)."""

    hour_limit: int
    hour_used: int
    day_limit: int
    day_used: int


class QuotaService:
    """Checks and counts questions per user, tokens per day, and active streams."""

    def __init__(
        self,
        store: BaseCache = cache,
        clock: Callable[[], datetime] = local_now,
    ) -> None:
        self._store = store
        self._clock = clock

    def _keys(self, user_id: object) -> tuple[str, str]:
        """Return the (hour, day) counter keys for the current local time."""
        now = self._clock()
        return f"q:{user_id}:h:{now:%Y%m%d%H}", f"q:{user_id}:d:{now:%Y%m%d}"

    def _token_key(self) -> str:
        """Return today's global token counter key."""
        return f"tok:{self._clock():%Y%m%d}"

    def _seconds_to_next_hour(self) -> int:
        """Seconds until the hourly window resets."""
        now = self._clock()
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return int((next_hour - now).total_seconds()) + 1

    def _seconds_to_tomorrow(self) -> int:
        """Seconds until the daily window resets (local midnight)."""
        now = self._clock()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return int((tomorrow - now).total_seconds()) + 1

    async def ausage(self, user_id: object) -> QuotaUsage:
        """Return the user's current hour/day usage.

        Args:
            user_id: The user's id.
        """
        hour_key, day_key = self._keys(user_id)
        return QuotaUsage(
            hour_limit=settings.CHAT_LIMIT_HOUR,
            hour_used=int(await self._store.aget(hour_key, 0)),
            day_limit=settings.CHAT_LIMIT_DAY,
            day_used=int(await self._store.aget(day_key, 0)),
        )

    def usage(self, user_id: object) -> QuotaUsage:
        """Sync variant of :meth:`ausage` for DRF views.

        Args:
            user_id: The user's id.
        """
        hour_key, day_key = self._keys(user_id)
        return QuotaUsage(
            hour_limit=settings.CHAT_LIMIT_HOUR,
            hour_used=int(self._store.get(hour_key, 0)),
            day_limit=settings.CHAT_LIMIT_DAY,
            day_used=int(self._store.get(day_key, 0)),
        )

    async def acheck(self, user_id: object) -> None:
        """Raise when the user or the whole service is over a limit.

        Args:
            user_id: The user's id.

        Raises:
            QuotaExceeded: Daily user limit or global token cap reached.
            RateLimited: Hourly user limit reached.
        """
        used = await self.ausage(user_id)
        if used.day_used >= used.day_limit:
            raise QuotaExceeded(retry_after=self._seconds_to_tomorrow(), scope="user")
        if int(await self._store.aget(self._token_key(), 0)) >= settings.GLOBAL_DAILY_TOKEN_CAP:
            raise QuotaExceeded(
                "The service reached its daily limit. Try again tomorrow.",
                retry_after=self._seconds_to_tomorrow(),
                scope="global",
            )
        if used.hour_used >= used.hour_limit:
            raise RateLimited(
                "Hourly question limit reached.", retry_after=self._seconds_to_next_hour()
            )

    async def _aincrement(self, key: str, amount: int, ttl: int) -> None:
        """Create the counter if missing, then add ``amount`` atomically."""
        await self._store.aadd(key, 0, ttl)
        await self._store.aincr(key, amount)

    async def aconsume(self, user_id: object) -> None:
        """Count one question for the user.

        Args:
            user_id: The user's id.
        """
        hour_key, day_key = self._keys(user_id)
        await self._aincrement(hour_key, 1, HOUR_TTL_S)
        await self._aincrement(day_key, 1, DAY_TTL_S)

    async def aadd_tokens(self, tokens: int) -> None:
        """Add tokens spent on Gemini to today's global counter.

        Args:
            tokens: Prompt + completion tokens of one answer.
        """
        if tokens > 0:
            await self._aincrement(self._token_key(), tokens, DAY_TTL_S)

    async def atokens_today(self) -> int:
        """Return the global tokens spent today."""
        return int(await self._store.aget(self._token_key(), 0))

    def tokens_today(self) -> int:
        """Sync variant of :meth:`atokens_today` for the admin dashboard."""
        return int(self._store.get(self._token_key(), 0))

    async def aacquire_stream(self, user_id: object) -> None:
        """Take the user's single stream lock.

        Args:
            user_id: The user's id.

        Raises:
            StreamInProgress: Another answer is still streaming.
        """
        if not await self._store.aadd(f"stream:{user_id}", 1, settings.STREAM_LOCK_TTL_S):
            raise StreamInProgress

    async def arelease_stream(self, user_id: object) -> None:
        """Release the user's stream lock (call in ``finally``).

        Args:
            user_id: The user's id.
        """
        await self._store.adelete(f"stream:{user_id}")
