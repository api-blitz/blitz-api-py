"""The Blitz API client implementation (async source; sync is generated alongside)."""

from __future__ import annotations

from functools import cached_property
from types import TracebackType
from typing import Any

import httpx

from . import _constants as C
from ._base_client import BaseClient, ResponseT, to_jsonable
from ._compat import AsyncSleep, TimeoutParam
from ._exceptions import APIConnectionError, APITimeoutError
from ._pagination_base import BasePage
from ._rate_limit import AsyncRateLimiter
from .resources import (
    AsyncAccountResource,
    AsyncEnrichmentResource,
    AsyncSearchResource,
    AsyncUtilsResource,
)


class AsyncBlitzAPI(BaseClient):
    """Client for the Blitz API.

    ``AsyncBlitzAPI`` is the async client and ``BlitzAPI`` is the sync client; both
    expose an identical method surface. See the ``blitz_api`` package docstring for a
    quickstart. (This docstring is shared with the generated sync client, so it stays
    flavour-neutral.)
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = C.DEFAULT_BASE_URL,
        timeout: float | httpx.Timeout = C.DEFAULT_TIMEOUT,
        max_retries: int = C.DEFAULT_MAX_RETRIES,
        rate_limit_rps: float | None = C.DEFAULT_RATE_LIMIT_RPS,
        http_client: httpx.AsyncClient | None = None,
        sleep: AsyncSleep | None = None,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url, max_retries=max_retries)
        if http_client is not None and timeout != C.DEFAULT_TIMEOUT:
            raise ValueError(
                "Pass `timeout` or `http_client`, not both: a supplied http_client carries "
                "its own timeout. Set the timeout on your httpx client instead."
            )
        self._http_client = http_client or httpx.AsyncClient(timeout=timeout)
        self._owns_http_client = http_client is None
        self._rate_limiter = AsyncRateLimiter(rate_limit_rps)
        if sleep is None:
            import asyncio

            sleep = asyncio.sleep
        self._sleep = sleep

    async def _request(
        self,
        method: str,
        path: str,
        *,
        body: Any | None,
        cast_to: type[ResponseT],
        timeout: TimeoutParam = None,
    ) -> ResponseT:
        url = self._build_url(path)
        headers = self._build_headers()
        json_body = to_jsonable(body) if body is not None else None

        attempt = 0
        while True:
            await self._rate_limiter.acquire()
            try:
                if timeout is None:
                    response = await self._http_client.request(
                        method, url, headers=headers, json=json_body
                    )
                else:
                    response = await self._http_client.request(
                        method, url, headers=headers, json=json_body, timeout=timeout
                    )
            except httpx.TimeoutException as exc:
                if self._should_retry_exception(exc) and attempt < self.max_retries:
                    attempt += 1
                    await self._sleep(self._backoff_seconds(attempt))
                    continue
                raise APITimeoutError(request=exc.request) from exc
            except httpx.RequestError as exc:
                if self._should_retry_exception(exc) and attempt < self.max_retries:
                    attempt += 1
                    await self._sleep(self._backoff_seconds(attempt))
                    continue
                raise APIConnectionError(
                    str(exc) or "Connection error.", request=exc.request
                ) from exc

            if response.is_success:
                result = self._parse_model(response, cast_to)
                if isinstance(result, BasePage):
                    result._bind(self, method, path, json_body, timeout)
                return result

            if self._should_retry(response.status_code) and attempt < self.max_retries:
                attempt += 1
                await self._sleep(self._retry_delay(response, attempt))
                continue

            raise self._make_status_error(response)

    async def close(self) -> None:
        """Close the underlying HTTP connection pool (if owned by this client)."""
        if self._owns_http_client:
            await self._http_client.aclose()

    async def __aenter__(self) -> AsyncBlitzAPI:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    @cached_property
    def account(self) -> AsyncAccountResource:
        return AsyncAccountResource(self)

    @cached_property
    def search(self) -> AsyncSearchResource:
        return AsyncSearchResource(self)

    @cached_property
    def enrichment(self) -> AsyncEnrichmentResource:
        return AsyncEnrichmentResource(self)

    @cached_property
    def utils(self) -> AsyncUtilsResource:
        return AsyncUtilsResource(self)
