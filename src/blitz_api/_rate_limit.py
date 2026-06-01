"""Client-side token-bucket rate limiters (sync + async).

The API enforces a per-key request rate (5 req/s by default). These limiters
throttle outgoing requests *before* they are sent so a single client instance
stays under the limit proactively; the server-side 429 retry path is the
backstop for bursts across processes.

Both limiters share a continuously-refilling token bucket. The clock and sleep
functions are injectable so tests can drive them with a fake clock.
"""

from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Awaitable, Callable


class RateLimiter:
    """Synchronous token-bucket limiter, safe to share across threads."""

    def __init__(
        self,
        rps: float | None,
        *,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.rps = rps
        self._capacity = max(rps, 1.0) if rps else 0.0
        self._tokens = self._capacity
        self._updated = monotonic()
        self._lock = threading.Lock()
        self._monotonic = monotonic
        self._sleep = sleep

    def acquire(self) -> None:
        """Block until a request token is available."""
        if not self.rps:
            return
        while True:
            with self._lock:
                now = self._monotonic()
                self._tokens = min(self._capacity, self._tokens + (now - self._updated) * self.rps)
                self._updated = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait = (1.0 - self._tokens) / self.rps
            self._sleep(wait)


class AsyncRateLimiter:
    """Asynchronous token-bucket limiter, safe to share across tasks."""

    def __init__(
        self,
        rps: float | None,
        *,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.rps = rps
        self._capacity = max(rps, 1.0) if rps else 0.0
        self._tokens = self._capacity
        self._updated = monotonic()
        self._lock = asyncio.Lock()
        self._monotonic = monotonic
        self._sleep = sleep

    async def acquire(self) -> None:
        """Suspend until a request token is available."""
        if not self.rps:
            return
        while True:
            async with self._lock:
                now = self._monotonic()
                self._tokens = min(self._capacity, self._tokens + (now - self._updated) * self.rps)
                self._updated = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait = (1.0 - self._tokens) / self.rps
            await self._sleep(wait)
