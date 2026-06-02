"""Tests for client construction, configuration, and request shaping."""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from blitz_api import AsyncBlitzAPI, BlitzAPI, BlitzError
from blitz_api._base_client import to_jsonable
from blitz_api._constants import API_KEY_ENV_VAR, API_KEY_HEADER
from blitz_api._rate_limit import RateLimiter
from blitz_api.types import Industry
from tests import data
from tests.conftest import FakeClock, url


def test_api_key_from_argument() -> None:
    client = BlitzAPI(api_key="explicit-key")
    assert client.api_key == "explicit-key"


def test_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(API_KEY_ENV_VAR, "env-key")
    client = BlitzAPI()
    assert client.api_key == "env-key"


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    with pytest.raises(BlitzError, match="No API key"):
        BlitzAPI()


def test_explicit_key_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(API_KEY_ENV_VAR, "env-key")
    client = BlitzAPI(api_key="explicit")
    assert client.api_key == "explicit"


def test_build_url_joins_path() -> None:
    client = BlitzAPI(api_key="k")
    assert (
        client._build_url("/v2/account/key-info") == "https://api.blitz-api.ai/v2/account/key-info"
    )
    assert (
        client._build_url("v2/account/key-info") == "https://api.blitz-api.ai/v2/account/key-info"
    )


def test_build_url_respects_custom_base() -> None:
    client = BlitzAPI(api_key="k", base_url="https://staging.example.com/")
    assert client._build_url("/v2/x") == "https://staging.example.com/v2/x"


def test_headers_include_key_and_user_agent() -> None:
    client = BlitzAPI(api_key="secret")
    headers = client._build_headers()
    assert headers[API_KEY_HEADER] == "secret"
    assert headers["Content-Type"] == "application/json"
    assert headers["User-Agent"].startswith("blitz-api-py/")


def test_resources_are_namespaced() -> None:
    client = BlitzAPI(api_key="k")
    assert type(client.account).__name__ == "AccountResource"
    assert type(client.search).__name__ == "SearchResource"
    assert type(client.enrichment).__name__ == "EnrichmentResource"
    assert type(client.utils).__name__ == "UtilsResource"
    # cached_property returns the same instance.
    assert client.account is client.account


def test_async_resources_are_namespaced() -> None:
    client = AsyncBlitzAPI(api_key="k")
    assert type(client.account).__name__ == "AsyncAccountResource"
    assert type(client.search).__name__ == "AsyncSearchResource"


def test_context_manager_closes_owned_client() -> None:
    with BlitzAPI(api_key="k") as client:
        http = client._http_client
    assert http.is_closed


def test_does_not_close_injected_client() -> None:
    http = httpx.Client()
    client = BlitzAPI(api_key="k", http_client=http)
    client.close()
    assert not http.is_closed
    http.close()


def test_http_client_and_timeout_together_raise() -> None:
    # Passing both is a silent footgun (the http_client carries its own timeout), so
    # the SDK rejects it explicitly instead of ignoring the timeout.
    with pytest.raises(ValueError, match="not both"):
        BlitzAPI(api_key="k", http_client=httpx.Client(), timeout=10.0)


def test_async_http_client_and_timeout_together_raise() -> None:
    with pytest.raises(ValueError, match="not both"):
        AsyncBlitzAPI(api_key="k", http_client=httpx.AsyncClient(), timeout=10.0)


def test_rate_limiter_throttles_through_request(httpx_mock: HTTPXMock, clock: FakeClock) -> None:
    # End-to-end: the limiter actually gates calls made through the client's request path.
    client = BlitzAPI(api_key="k", rate_limit_rps=2)
    client._rate_limiter = RateLimiter(2, monotonic=clock.monotonic, sleep=clock.sleep)
    for _ in range(3):
        httpx_mock.add_response(url=url("/v2/account/key-info"), method="GET", json=data.KEY_INFO)

    for _ in range(3):
        client.account.key_info()

    assert clock.slept == [1.0]  # 3rd call waits out the 2-rps window


async def test_async_context_manager_closes_owned_client() -> None:
    async with AsyncBlitzAPI(api_key="k") as client:
        http = client._http_client
    assert http.is_closed


class TestToJsonable:
    def test_resolves_enums(self) -> None:
        assert to_jsonable(Industry.BANKING) == "Banking"

    def test_drops_none_values(self) -> None:
        assert to_jsonable({"a": 1, "b": None}) == {"a": 1}

    def test_keeps_falsy_non_none(self) -> None:
        assert to_jsonable({"min": 0, "items": []}) == {"min": 0, "items": []}

    def test_recurses_into_nested_structures(self) -> None:
        payload = {
            "company": {"industry": {"include": [Industry.SOFTWARE_DEVELOPMENT]}, "skip": None},
            "tiers": [{"include_title": ["CEO"], "exclude_title": None}],
        }
        assert to_jsonable(payload) == {
            "company": {"industry": {"include": ["Software Development"]}},
            "tiers": [{"include_title": ["CEO"]}],
        }
