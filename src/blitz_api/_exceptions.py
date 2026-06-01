"""Exception hierarchy raised by the Blitz API SDK.

::

    BlitzError
    ├── APIConnectionError        # request never completed (network / timeout)
    │   └── APITimeoutError
    └── APIStatusError            # a non-2xx HTTP response was received
        ├── AuthenticationError       # 401
        ├── InsufficientCreditsError  # 402
        ├── NotFoundError             # 404
        ├── RateLimitError            # 429 (after retries are exhausted)
        └── ServerError               # 5xx (after retries are exhausted)

Catch :class:`BlitzError` to handle anything this SDK raises.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import httpx


class BlitzError(Exception):
    """Base class for every error raised by this SDK."""


class APIConnectionError(BlitzError):
    """The request could not be completed (connection error, DNS, etc.)."""

    def __init__(
        self, message: str = "Connection error.", *, request: httpx.Request | None = None
    ) -> None:
        super().__init__(message)
        self.request = request


class APITimeoutError(APIConnectionError):
    """The request timed out."""

    def __init__(self, *, request: httpx.Request | None = None) -> None:
        super().__init__("Request timed out.", request=request)


class APIStatusError(BlitzError):
    """The API returned a non-success HTTP status code.

    Attributes:
        status_code: The HTTP status code of the response.
        body: The parsed JSON body, or the raw text if it was not JSON.
        message: A human-readable message extracted from the body when present.
        request_id: The value of the ``x-request-id`` response header, if any.
        response: The underlying :class:`httpx.Response`.
    """

    def __init__(
        self,
        message: str,
        *,
        response: httpx.Response,
        body: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.response = response
        self.status_code = response.status_code
        self.body = body
        self.request_id = response.headers.get("x-request-id")


class AuthenticationError(APIStatusError):
    """401 — the API key is missing or invalid."""


class InsufficientCreditsError(APIStatusError):
    """402 — the key is valid but the account is out of credits."""


class NotFoundError(APIStatusError):
    """404 — the API key or resource does not exist."""


class RateLimitError(APIStatusError):
    """429 — too many requests (raised only after retries are exhausted)."""


class ServerError(APIStatusError):
    """5xx — the API failed (raised only after retries are exhausted)."""
