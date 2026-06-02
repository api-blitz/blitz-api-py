"""Tests for the retry / backoff policy of both clients."""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from blitz_api import (
    APIConnectionError,
    APITimeoutError,
    AsyncBlitzAPI,
    AuthenticationError,
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


def test_429_retry_after_is_capped(httpx_mock: HTTPXMock, sleeps: SleepRecorder) -> None:
    # A pathologically large Retry-After is clamped so the client can't sleep for hours.
    httpx_mock.add_response(status_code=429, headers={"Retry-After": "86400"})
    httpx_mock.add_response(status_code=200, json=data.KEY_INFO)

    client = _sync_client(sleeps)
    client.account.key_info()

    assert sleeps.calls == [120.0]  # MAX_RETRY_WAIT_SECONDS


def test_429_retry_after_http_date(httpx_mock: HTTPXMock, sleeps: SleepRecorder) -> None:
    # An HTTP-date Retry-After is parsed; a date in the past resolves to wait now (0s).
    httpx_mock.add_response(
        status_code=429, headers={"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}
    )
    httpx_mock.add_response(status_code=200, json=data.KEY_INFO)

    client = _sync_client(sleeps)
    client.account.key_info()

    assert sleeps.calls == [0.0]


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


def test_read_timeout_is_not_retried(httpx_mock: HTTPXMock, sleeps: SleepRecorder) -> None:
    # A read timeout may mean the server already received (and billed) the request, so
    # it is surfaced immediately rather than retried — retrying could double-charge.
    httpx_mock.add_exception(httpx.ReadTimeout("read timed out"))

    client = _sync_client(sleeps)
    with pytest.raises(APITimeoutError):
        client.account.key_info()

    assert len(httpx_mock.get_requests()) == 1
    assert sleeps.calls == []


def test_connect_timeout_retries_then_raises(httpx_mock: HTTPXMock, sleeps: SleepRecorder) -> None:
    # A connect timeout means nothing reached the server, so retrying is safe.
    for _ in range(3):
        httpx_mock.add_exception(httpx.ConnectTimeout("connect timed out"))

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


def _async_client(sleeps: SleepRecorder, *, max_retries: int = 2) -> AsyncBlitzAPI:
    return AsyncBlitzAPI(
        api_key="k", rate_limit_rps=None, max_retries=max_retries, sleep=sleeps.asynchronous
    )


async def test_async_retries_5xx_then_succeeds(
    httpx_mock: HTTPXMock, sleeps: SleepRecorder
) -> None:
    httpx_mock.add_response(status_code=500, json={"message": "boom"})
    httpx_mock.add_response(status_code=200, json=data.KEY_INFO)

    client = _async_client(sleeps)
    info = await client.account.key_info()

    assert info.valid is True
    assert len(httpx_mock.get_requests()) == 2
    assert len(sleeps.calls) == 1
    await client.close()


async def test_async_5xx_exhausts_and_raises_server_error(
    httpx_mock: HTTPXMock, sleeps: SleepRecorder
) -> None:
    for _ in range(3):
        httpx_mock.add_response(status_code=503, json={"message": "unavailable"})

    client = _async_client(sleeps)
    with pytest.raises(ServerError):
        await client.account.key_info()
    assert len(httpx_mock.get_requests()) == 3
    await client.close()


async def test_async_429_exhausts_and_raises_rate_limit(
    httpx_mock: HTTPXMock, sleeps: SleepRecorder
) -> None:
    for _ in range(3):
        httpx_mock.add_response(status_code=429, json={"message": "slow down"})

    client = _async_client(sleeps)
    with pytest.raises(RateLimitError):
        await client.account.key_info()
    assert sleeps.calls == [60.0, 60.0]
    await client.close()


async def test_async_read_timeout_is_not_retried(
    httpx_mock: HTTPXMock, sleeps: SleepRecorder
) -> None:
    httpx_mock.add_exception(httpx.ReadTimeout("read timed out"))

    client = _async_client(sleeps)
    with pytest.raises(APITimeoutError):
        await client.account.key_info()
    assert len(httpx_mock.get_requests()) == 1
    assert sleeps.calls == []
    await client.close()


async def test_async_connect_timeout_retries_then_raises(
    httpx_mock: HTTPXMock, sleeps: SleepRecorder
) -> None:
    for _ in range(3):
        httpx_mock.add_exception(httpx.ConnectTimeout("connect timed out"))

    client = _async_client(sleeps)
    with pytest.raises(APITimeoutError):
        await client.account.key_info()
    assert len(httpx_mock.get_requests()) == 3
    await client.close()


async def test_async_client_error_is_not_retried(
    httpx_mock: HTTPXMock, sleeps: SleepRecorder
) -> None:
    httpx_mock.add_response(status_code=401, json={"message": "nope"})

    client = _async_client(sleeps)
    with pytest.raises(AuthenticationError):
        await client.account.key_info()
    assert len(httpx_mock.get_requests()) == 1
    assert sleeps.calls == []
    await client.close()
