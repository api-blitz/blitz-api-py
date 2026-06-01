"""The public Blitz API clients: :class:`BlitzAPI` (sync) and :class:`AsyncBlitzAPI`."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from functools import cached_property
from types import TracebackType
from typing import Any

import httpx

from . import _constants as C
from ._base_client import BaseClient, ResponseT, to_jsonable
from ._exceptions import APIConnectionError, APITimeoutError
from ._rate_limit import AsyncRateLimiter, RateLimiter
from .resources import (
    AccountResource,
    AsyncAccountResource,
    AsyncEnrichmentResource,
    AsyncSearchResource,
    AsyncUtilsResource,
    EnrichmentResource,
    SearchResource,
    UtilsResource,
)


class BlitzAPI(BaseClient):
    """Synchronous client for the Blitz API.

    Example::

        from blitz_api import BlitzAPI

        with BlitzAPI() as client:          # reads BLITZ_API_KEY
            info = client.account.key_info()
            result = client.enrichment.email(
                person_linkedin_url="https://www.linkedin.com/in/example",
            )
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = C.DEFAULT_BASE_URL,
        timeout: float | httpx.Timeout = C.DEFAULT_TIMEOUT,
        max_retries: int = C.DEFAULT_MAX_RETRIES,
        rate_limit_rps: float | None = C.DEFAULT_RATE_LIMIT_RPS,
        http_client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url, max_retries=max_retries)
        self._http_client = http_client or httpx.Client(timeout=timeout)
        self._owns_http_client = http_client is None
        self._rate_limiter = RateLimiter(rate_limit_rps)
        self._sleep = sleep

    def _request(
        self, method: str, path: str, *, body: Any | None, cast_to: type[ResponseT]
    ) -> ResponseT:
        url = self._build_url(path)
        headers = self._build_headers()
        json_body = to_jsonable(body) if body is not None else None

        attempt = 0
        while True:
            self._rate_limiter.acquire()
            try:
                response = self._http_client.request(method, url, headers=headers, json=json_body)
            except httpx.TimeoutException as exc:
                if attempt < self.max_retries:
                    attempt += 1
                    self._sleep(self._backoff_seconds(attempt))
                    continue
                raise APITimeoutError(request=exc.request) from exc
            except httpx.RequestError as exc:
                if attempt < self.max_retries:
                    attempt += 1
                    self._sleep(self._backoff_seconds(attempt))
                    continue
                raise APIConnectionError(
                    str(exc) or "Connection error.", request=exc.request
                ) from exc

            if response.is_success:
                return self._parse_model(response, cast_to)

            if self._should_retry(response.status_code) and attempt < self.max_retries:
                attempt += 1
                self._sleep(self._retry_delay(response, attempt))
                continue

            raise self._make_status_error(response)

    def close(self) -> None:
        """Close the underlying HTTP connection pool (if owned by this client)."""
        if self._owns_http_client:
            self._http_client.close()

    def __enter__(self) -> BlitzAPI:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    @cached_property
    def account(self) -> AccountResource:
        return AccountResource(self)

    @cached_property
    def search(self) -> SearchResource:
        return SearchResource(self)

    @cached_property
    def enrichment(self) -> EnrichmentResource:
        return EnrichmentResource(self)

    @cached_property
    def utils(self) -> UtilsResource:
        return UtilsResource(self)


class AsyncBlitzAPI(BaseClient):
    """Asynchronous client for the Blitz API.

    Example::

        from blitz_api import AsyncBlitzAPI

        async with AsyncBlitzAPI() as client:
            info = await client.account.key_info()
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
        sleep: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url, max_retries=max_retries)
        self._http_client = http_client or httpx.AsyncClient(timeout=timeout)
        self._owns_http_client = http_client is None
        self._rate_limiter = AsyncRateLimiter(rate_limit_rps)
        if sleep is None:
            import asyncio

            sleep = asyncio.sleep
        self._sleep = sleep

    async def _request(
        self, method: str, path: str, *, body: Any | None, cast_to: type[ResponseT]
    ) -> ResponseT:
        url = self._build_url(path)
        headers = self._build_headers()
        json_body = to_jsonable(body) if body is not None else None

        attempt = 0
        while True:
            await self._rate_limiter.acquire()
            try:
                response = await self._http_client.request(
                    method, url, headers=headers, json=json_body
                )
            except httpx.TimeoutException as exc:
                if attempt < self.max_retries:
                    attempt += 1
                    await self._sleep(self._backoff_seconds(attempt))
                    continue
                raise APITimeoutError(request=exc.request) from exc
            except httpx.RequestError as exc:
                if attempt < self.max_retries:
                    attempt += 1
                    await self._sleep(self._backoff_seconds(attempt))
                    continue
                raise APIConnectionError(
                    str(exc) or "Connection error.", request=exc.request
                ) from exc

            if response.is_success:
                return self._parse_model(response, cast_to)

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
