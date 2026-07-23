"""The Utilities resource: ``client.utils``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..._compat import TimeoutParam
from ...types.utils import CurrentDateResponse

if TYPE_CHECKING:
    from ..._client import AsyncBlitzAPI

_CURRENT_DATE = "/v2/utils/current-date"


class AsyncUtilsResource:
    def __init__(self, client: AsyncBlitzAPI) -> None:
        self._client = client

    async def current_date(
        self, *, region: str | None = None, timeout: TimeoutParam = None
    ) -> CurrentDateResponse:
        """Get the current server date/time for an IANA timezone (e.g. ``America/New_York``).

        ``region`` is optional; the server defaults to ``America/New_York`` when omitted.
        """
        body: dict[str, Any] = {} if region is None else {"region": region}
        return await self._client._request(
            "POST",
            _CURRENT_DATE,
            body=body,
            cast_to=CurrentDateResponse,
            timeout=timeout,
        )
