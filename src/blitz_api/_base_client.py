"""Shared, IO-free request-pipeline logic for the sync and async clients.

The actual network calls live in :mod:`blitz_api._client`; everything here is
pure so both clients share identical header building, retry decisions, backoff
computation, error mapping, and response parsing.
"""

from __future__ import annotations

import os
import random
from enum import Enum
from typing import Any, TypeVar, cast
from urllib.parse import urljoin

import httpx

from . import _constants as C
from ._exceptions import (
    APIStatusError,
    AuthenticationError,
    BlitzError,
    InsufficientCreditsError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from .types._models import BlitzModel

ResponseT = TypeVar("ResponseT", bound=BlitzModel)

# Status code -> exception class. Anything not listed that is still non-2xx
# falls back to a generic APIStatusError (or ServerError for any 5xx).
_STATUS_EXCEPTIONS: dict[int, type[APIStatusError]] = {
    401: AuthenticationError,
    402: InsufficientCreditsError,
    404: NotFoundError,
    429: RateLimitError,
}


def to_jsonable(value: Any) -> Any:
    """Recursively prepare a request payload for JSON serialization.

    Resolves :class:`enum.Enum` members to their values and drops ``None`` so
    that optional, unset fields are simply omitted from the request body.
    """
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        mapping = cast("dict[str, Any]", value)
        return {k: to_jsonable(v) for k, v in mapping.items() if v is not None}
    if isinstance(value, (list, tuple)):
        sequence = cast("list[Any]", value)
        return [to_jsonable(v) for v in sequence]
    return value


class BaseClient:
    """Configuration and pure helpers shared by both clients."""

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str,
        max_retries: int,
    ) -> None:
        resolved = api_key if api_key is not None else os.environ.get(C.API_KEY_ENV_VAR)
        if not resolved:
            raise BlitzError(
                "No API key provided. Pass api_key=... or set the "
                f"{C.API_KEY_ENV_VAR} environment variable."
            )
        self.api_key = resolved
        self.base_url = base_url.rstrip("/") + "/"
        self.max_retries = max_retries

    # -- request shaping -------------------------------------------------

    def _build_url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    def _build_headers(self) -> dict[str, str]:
        return {
            C.API_KEY_HEADER: self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": C.USER_AGENT,
        }

    # -- retry policy ----------------------------------------------------

    @staticmethod
    def _should_retry(status_code: int) -> bool:
        return status_code == 429 or status_code >= 500

    def _backoff_seconds(self, attempt: int) -> float:
        """Exponential backoff with full jitter (attempt starts at 1)."""
        base = min(8.0, 0.5 * 2.0 ** (attempt - 1))
        return base + random.uniform(0.0, 0.5)

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        if response.status_code == 429:
            retry_after = response.headers.get("retry-after")
            if retry_after:
                try:
                    return float(retry_after)
                except ValueError:
                    pass
            return C.DEFAULT_RETRY_AFTER_SECONDS
        return self._backoff_seconds(attempt)

    # -- response handling ----------------------------------------------

    @staticmethod
    def _parse_body(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text

    def _make_status_error(self, response: httpx.Response) -> APIStatusError:
        body: Any = self._parse_body(response)
        message: str | None = None
        if isinstance(body, dict):
            mapping = cast("dict[str, Any]", body)
            raw = mapping.get("message") or mapping.get("error")
            if isinstance(raw, str):
                message = raw
        if message is None:
            message = f"HTTP {response.status_code} from {response.request.url}"

        exc_class = _STATUS_EXCEPTIONS.get(response.status_code)
        if exc_class is None:
            exc_class = ServerError if response.status_code >= 500 else APIStatusError
        return exc_class(message, response=response, body=cast("Any", body))

    @staticmethod
    def _parse_model(response: httpx.Response, cast_to: type[ResponseT]) -> ResponseT:
        return cast_to.model_validate(response.json())
