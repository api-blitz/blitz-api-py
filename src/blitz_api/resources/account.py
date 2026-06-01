"""The Account resource: ``client.account``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..types.account import KeyInfo

if TYPE_CHECKING:
    from .._client import AsyncBlitzAPI, BlitzAPI

_KEY_INFO_PATH = "/v2/account/key-info"


class AccountResource:
    def __init__(self, client: BlitzAPI) -> None:
        self._client = client

    def key_info(self) -> KeyInfo:
        """Check the API key's validity, credit balance, and rate limit.

        A cheap health check to run before a batch job.
        """
        return self._client._request("GET", _KEY_INFO_PATH, body=None, cast_to=KeyInfo)


class AsyncAccountResource:
    def __init__(self, client: AsyncBlitzAPI) -> None:
        self._client = client

    async def key_info(self) -> KeyInfo:
        """Check the API key's validity, credit balance, and rate limit."""
        return await self._client._request("GET", _KEY_INFO_PATH, body=None, cast_to=KeyInfo)
