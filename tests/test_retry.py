"""Tests for the retry / backoff policy of both clients."""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from blitz_api import (
    APIConnectionError,
    APITimeoutError,
    AsyncBlitzAPI,
    BlitzAPI,
    RateLimitError,
    ServerError,
)
from tests import data
from tests.conftest import SleepRecorder


def _sync_client(sleeps: SleepRecorder, *, max_retries: int = 2) -> BlitzAPI:
    return BlitzAPI(api_key="k", rate_limit_rps=None, max_retries=max_retries, sleep=sleeps.sync)


def test_retries_5xx_then_succeeds(httpx_mock: HTTPXMock, sleeps: SleepRecorder) -> None:
    httpx_mock.add_response(status_code=500, json={"message": "boom"})
    httpx_mock.add_response(status_code=500, json={"message": "boom"})
    httpx_mock.add_response(status_code=200, json=data.KEY_INFO)

    client = _sync_client(sleeps)
    info = client.account.key_info()

    assert info.valid is True
    assert len(httpx_mock.get_requests()) == 3
    assert len(sleeps.calls) == 2  # one wait between each of the three attempts


def test_5xx_exhausts_retries_and_raises_server_error(
    httpx_mock: HTTPXMock, sleeps: SleepRecorder
) -> None:
    for _ in range(3):
        httpx_mock.add_response(status_code=503, json={"message": "unavailable"})

    client = _sync_client(sleeps)
    with pytest.raises(ServerError) as exc_info:
        client.account.key_info()

    assert exc_info.value.status_code == 503
    assert len(httpx_mock.get_requests()) == 3
    assert len(sleeps.calls) == 2


def test_429_waits_default_60s_when_no_retry_after(
    httpx_mock: HTTPXMock, sleeps: SleepRecorder
) -> None:
    for _ in range(3):
        httpx_mock.add_response(status_code=429, json={"message": "slow down"})

    client = _sync_client(sleeps)
    with pytest.raises(RateLimitError):
        client.account.key_info()

    assert sleeps.calls == [60.0, 60.0]


def test_429_respects_retry_after_header(httpx_mock: HTTPXMock, sleeps: SleepRecorder) -> None:
    httpx_mock.add_response(status_code=429, headers={"Retry-After": "2"})
    httpx_mock.add_response(status_code=200, json=data.KEY_INFO)

    client = _sync_client(sleeps)
    client.account.key_info()

    assert sleeps.calls == [2.0]


@pytest.mark.parametrize("status", [400, 401, 402, 404])
def test_client_errors_are_not_retried(
    httpx_mock: HTTPXMock, sleeps: SleepRecorder, status: int
) -> None:
    httpx_mock.add_response(status_code=status, json={"message": "nope"})

    client = _sync_client(sleeps)
    with pytest.raises(Exception):  # noqa: B017 - exact type covered in test_exceptions
        client.account.key_info()

    assert len(httpx_mock.get_requests()) == 1
    assert sleeps.calls == []


def test_timeout_retries_then_raises(httpx_mock: HTTPXMock, sleeps: SleepRecorder) -> None:
    for _ in range(3):
        httpx_mock.add_exception(httpx.TimeoutException("timed out"))

    client = _sync_client(sleeps)
    with pytest.raises(APITimeoutError):
        client.account.key_info()

    assert len(httpx_mock.get_requests()) == 3
    assert len(sleeps.calls) == 2


def test_connection_error_retries_then_raises(httpx_mock: HTTPXMock, sleeps: SleepRecorder) -> None:
    for _ in range(3):
        httpx_mock.add_exception(httpx.ConnectError("refused"))

    client = _sync_client(sleeps)
    with pytest.raises(APIConnectionError):
        client.account.key_info()

    assert len(httpx_mock.get_requests()) == 3


def test_max_retries_zero_makes_one_attempt(httpx_mock: HTTPXMock, sleeps: SleepRecorder) -> None:
    httpx_mock.add_response(status_code=500, json={"message": "boom"})

    client = _sync_client(sleeps, max_retries=0)
    with pytest.raises(ServerError):
        client.account.key_info()

    assert len(httpx_mock.get_requests()) == 1
    assert sleeps.calls == []


async def test_async_retries_5xx_then_succeeds(
    httpx_mock: HTTPXMock, sleeps: SleepRecorder
) -> None:
    httpx_mock.add_response(status_code=500, json={"message": "boom"})
    httpx_mock.add_response(status_code=200, json=data.KEY_INFO)

    client = AsyncBlitzAPI(
        api_key="k", rate_limit_rps=None, max_retries=2, sleep=sleeps.asynchronous
    )
    info = await client.account.key_info()

    assert info.valid is True
    assert len(httpx_mock.get_requests()) == 2
    assert len(sleeps.calls) == 1
    await client.close()
