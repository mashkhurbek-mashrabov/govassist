"""Server-Sent Events framing and keep-alive pings (contract §4)."""

import asyncio
import json
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any

from apps.chat.constants import PING


@dataclass(frozen=True)
class Event:
    """One stream event: meta, status, office, delta, final, error or done."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)


_END = Event("__end__")


def format_event(name: str, data: dict[str, Any]) -> str:
    r"""Frame one event on the wire.

    Args:
        name: Event name.
        data: JSON payload.

    Returns:
        ``event: <name>\\ndata: <json>\\n\\n``.
    """
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {name}\ndata: {payload}\n\n"


async def _produce(events: AsyncGenerator[Event], queue: asyncio.Queue[Event]) -> None:
    """Run the whole event generator in one task, pushing events to ``queue``.

    Closing ``events`` in ``finally`` makes its cleanup run even when the task is cancelled
    while the generator waits at a ``yield``.
    """
    try:
        async for event in events:
            queue.put_nowait(event)
    finally:
        await events.aclose()
        queue.put_nowait(_END)


async def sse_stream(events: AsyncGenerator[Event], *, interval: float) -> AsyncIterator[str]:
    """Format events and send ``: ping`` after ``interval`` s of silence.

    A client disconnect cancels this stream; the producer task is then cancelled too, so
    the answer generator's own handlers (mark the message stopped, release the lock) run.

    Args:
        events: The answer events.
        interval: Seconds of silence before a ping.
    """
    queue: asyncio.Queue[Event] = asyncio.Queue()
    producer = asyncio.create_task(_produce(events, queue))
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=interval)
            except TimeoutError:
                yield PING
                continue
            if event is _END:
                break
            yield format_event(event.name, event.data)
        await producer
    finally:
        if not producer.done():
            producer.cancel()
            with suppress(asyncio.CancelledError):
                await producer
