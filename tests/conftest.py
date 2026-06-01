"""Shared pytest fixtures and helpers."""

from __future__ import annotations

import httpx
import pytest

from blitz_api import AsyncBlitzAPI, BlitzAPI

BASE_URL = "https://api.blitz-api.ai"
TEST_KEY = "test-key"


def url(path: str) -> str:
    return f"{BASE_URL}{path}"


@pytest.fixture
def sync_client() -> BlitzAPI:
    """A sync client with client-side rate limiting disabled (no test delays)."""
    return BlitzAPI(api_key=TEST_KEY, rate_limit_rps=None)


@pytest.fixture
async def async_client() -> AsyncBlitzAPI:
    """An async client with client-side rate limiting disabled."""
    return AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None)


class SleepRecorder:
    """Records the durations passed to a (sync or async) sleep stand-in."""

    def __init__(self) -> None:
        self.calls: list[float] = []

    def sync(self, seconds: float) -> None:
        self.calls.append(seconds)

    async def asynchronous(self, seconds: float) -> None:
        self.calls.append(seconds)


@pytest.fixture
def sleeps() -> SleepRecorder:
    return SleepRecorder()


class FakeClock:
    """A controllable monotonic clock + sleep, for rate-limiter tests."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.slept: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds

    async def asleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def make_request(method: str = "GET", target: str = "/") -> httpx.Request:
    return httpx.Request(method, url(target))
