"""Tests for status-code -> exception mapping and error attributes."""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from blitz_api import (
    APIResponseValidationError,
    APIStatusError,
    AuthenticationError,
    BlitzAPI,
    BlitzError,
    InsufficientCreditsError,
    NotFoundError,
)


def _client() -> BlitzAPI:
    return BlitzAPI(api_key="k", rate_limit_rps=None, max_retries=0)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, AuthenticationError),
        (402, InsufficientCreditsError),
        (404, NotFoundError),
        (400, APIStatusError),
        (418, APIStatusError),
    ],
)
def test_status_maps_to_exception(
    httpx_mock: HTTPXMock, status: int, expected: type[BlitzError]
) -> None:
    httpx_mock.add_response(status_code=status, json={"message": "explain"})
    with pytest.raises(expected) as exc_info:
        _client().account.key_info()
    # Every status error subclasses APIStatusError and BlitzError.
    assert isinstance(exc_info.value, APIStatusError)
    assert isinstance(exc_info.value, BlitzError)


def test_error_carries_status_body_and_message(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        status_code=402,
        json={"message": "Insufficient credits balance"},
        headers={"x-request-id": "req_123"},
    )
    with pytest.raises(InsufficientCreditsError) as exc_info:
        _client().account.key_info()

    err = exc_info.value
    assert err.status_code == 402
    assert err.message == "Insufficient credits balance"
    assert err.body == {"message": "Insufficient credits balance"}
    assert err.request_id == "req_123"


def test_error_message_falls_back_when_body_has_none(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=500, text="upstream exploded")
    with pytest.raises(APIStatusError) as exc_info:
        _client().account.key_info()
    assert "500" in exc_info.value.message
    assert exc_info.value.body == "upstream exploded"


def test_non_json_2xx_raises_response_validation_error(httpx_mock: HTTPXMock) -> None:
    # A 200 with a non-JSON body (e.g. a proxy's HTML) stays inside BlitzError.
    httpx_mock.add_response(status_code=200, text="<html>not json</html>")
    with pytest.raises(APIResponseValidationError) as exc_info:
        _client().account.key_info()
    assert exc_info.value.status_code == 200
    assert isinstance(exc_info.value, BlitzError)


def test_empty_2xx_body_raises_response_validation_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200, content=b"")
    with pytest.raises(APIResponseValidationError):
        _client().account.key_info()


def test_wrong_shape_2xx_raises_response_validation_error(httpx_mock: HTTPXMock) -> None:
    # Valid JSON that doesn't match the model (a list, not an object) is wrapped too.
    httpx_mock.add_response(status_code=200, json=["unexpected", "list"])
    with pytest.raises(APIResponseValidationError):
        _client().account.key_info()
