"""Tests for the token-bucket rate limiters (driven by a fake clock)."""

from __future__ import annotations

from blitz_api._rate_limit import AsyncRateLimiter, RateLimiter
from tests.conftest import FakeClock


def test_disabled_limiter_never_sleeps(clock: FakeClock) -> None:
    limiter = RateLimiter(None, monotonic=clock.monotonic, sleep=clock.sleep)
    for _ in range(100):
        limiter.acquire()
    assert clock.slept == []


def test_burst_up_to_capacity_is_immediate(clock: FakeClock) -> None:
    limiter = RateLimiter(5, monotonic=clock.monotonic, sleep=clock.sleep)
    for _ in range(5):
        limiter.acquire()
    assert clock.slept == []


def test_exceeding_capacity_waits(clock: FakeClock) -> None:
    limiter = RateLimiter(5, monotonic=clock.monotonic, sleep=clock.sleep)
    for _ in range(5):
        limiter.acquire()
    limiter.acquire()  # 6th — bucket empty, must wait 1/5 s for one token
    assert clock.slept == [0.2]


def test_wait_scales_with_rate(clock: FakeClock) -> None:
    limiter = RateLimiter(2, monotonic=clock.monotonic, sleep=clock.sleep)
    for _ in range(2):
        limiter.acquire()
    limiter.acquire()
    assert clock.slept == [0.5]


async def test_async_burst_is_immediate(clock: FakeClock) -> None:
    limiter = AsyncRateLimiter(5, monotonic=clock.monotonic, sleep=clock.asleep)
    for _ in range(5):
        await limiter.acquire()
    assert clock.slept == []


async def test_async_exceeding_capacity_waits(clock: FakeClock) -> None:
    limiter = AsyncRateLimiter(5, monotonic=clock.monotonic, sleep=clock.asleep)
    for _ in range(5):
        await limiter.acquire()
    await limiter.acquire()
    assert clock.slept == [0.2]
