"""Tests for the sliding-window rate limiters (driven by a fake clock)."""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from blitz_api import AsyncBlitzAPI, BlitzAPI
from blitz_api._rate_limit import AsyncRateLimiter, RateLimiter
from tests import data
from tests.conftest import FakeClock


class _SleepCalled(Exception):
    """Raised by the injected sleep to prove the limiter called it (and stop the loop)."""


def test_disabled_limiter_never_sleeps(clock: FakeClock) -> None:
    limiter = RateLimiter(None, monotonic=clock.monotonic, sleep=clock.sleep)
    for _ in range(100):
        limiter.acquire()
    assert clock.slept == []


def test_burst_up_to_rps_is_immediate(clock: FakeClock) -> None:
    limiter = RateLimiter(5, monotonic=clock.monotonic, sleep=clock.sleep)
    for _ in range(5):
        limiter.acquire()
    assert clock.slept == []


def test_exceeding_rps_waits_for_window(clock: FakeClock) -> None:
    limiter = RateLimiter(5, monotonic=clock.monotonic, sleep=clock.sleep)
    for _ in range(5):
        limiter.acquire()  # all admitted at the same instant
    limiter.acquire()  # 6th: wait until the oldest send leaves the 1s window
    assert clock.slept == [1.0]


def test_window_slides_so_requests_resume(clock: FakeClock) -> None:
    # Once a full window has elapsed, the limiter admits another burst with no wait.
    limiter = RateLimiter(2, monotonic=clock.monotonic, sleep=clock.sleep)
    limiter.acquire()
    limiter.acquire()  # 2 admitted at t0
    clock.now += 1.0  # advance past the window without the limiter sleeping
    limiter.acquire()
    limiter.acquire()
    assert clock.slept == []  # earlier sends aged out of the window


def test_never_exceeds_rps_in_any_window(clock: FakeClock) -> None:
    # The key property a token bucket failed: no first-second overshoot.
    limiter = RateLimiter(3, monotonic=clock.monotonic, sleep=clock.sleep)
    start = clock.now
    for _ in range(7):
        limiter.acquire()
    # 7 requests at 3 rps: first 3 immediate, then 2 more waits of a full window each.
    assert clock.slept == [1.0, 1.0]
    assert clock.now - start == 2.0


def test_fractional_rps_floors_to_integer_budget(clock: FakeClock) -> None:
    # rps is typed float; a fractional rate floors to a whole-request budget (here 2),
    # so the 3rd request in a window waits rather than overshooting on the `< rps` compare.
    limiter = RateLimiter(2.5, monotonic=clock.monotonic, sleep=clock.sleep)
    for _ in range(2):
        limiter.acquire()
    limiter.acquire()
    assert clock.slept == [1.0]


def test_sub_one_rps_admits_one_per_window_without_stalling(clock: FakeClock) -> None:
    # A budget floored to <1 would deadlock (`len < 0` never true); it must clamp to 1.
    limiter = RateLimiter(0.5, monotonic=clock.monotonic, sleep=clock.sleep)
    limiter.acquire()  # admitted immediately, not hung
    limiter.acquire()  # 2nd waits out the window
    assert clock.slept == [1.0]


async def test_async_burst_is_immediate(clock: FakeClock) -> None:
    limiter = AsyncRateLimiter(5, monotonic=clock.monotonic, sleep=clock.asleep)
    for _ in range(5):
        await limiter.acquire()
    assert clock.slept == []


async def test_async_exceeding_rps_waits_for_window(clock: FakeClock) -> None:
    limiter = AsyncRateLimiter(5, monotonic=clock.monotonic, sleep=clock.asleep)
    for _ in range(5):
        await limiter.acquire()
    await limiter.acquire()
    assert clock.slept == [1.0]


def test_sync_client_threads_its_sleep_into_per_endpoint_limiter(httpx_mock: HTTPXMock) -> None:
    # The client's ``sleep`` must drive the limiter's throttle wait, not just retry backoff:
    # a custom sleep injected for tests has to reach the per-endpoint limiter too. With the
    # default ``time.sleep`` the limiter would block ~1s on the 2nd call (or hang under a
    # no-op fake); raising from our sleep proves the limiter invoked *it*.
    calls: list[float] = []

    def fake_sleep(seconds: float) -> None:
        calls.append(seconds)
        raise _SleepCalled

    httpx_mock.add_response(json=data.KEY_INFO)  # only the 1st call reaches the network
    client = BlitzAPI(api_key="k", rate_limit_rps=1, sleep=fake_sleep)

    client.account.key_info()  # admitted immediately, fills the 1-req window
    with pytest.raises(_SleepCalled):
        client.account.key_info()  # 2nd: limiter throttles → calls our sleep → raises

    assert calls and calls[0] > 0


async def test_async_client_threads_its_sleep_into_per_endpoint_limiter(
    httpx_mock: HTTPXMock,
) -> None:
    calls: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        calls.append(seconds)
        raise _SleepCalled

    httpx_mock.add_response(json=data.KEY_INFO)  # only the 1st call reaches the network
    client = AsyncBlitzAPI(api_key="k", rate_limit_rps=1, sleep=fake_sleep)

    await client.account.key_info()  # admitted immediately, fills the 1-req window
    with pytest.raises(_SleepCalled):
        await client.account.key_info()  # 2nd: limiter throttles → calls our sleep → raises

    assert calls and calls[0] > 0
    await client.close()
