"""Exception hierarchy raised by the Blitz API SDK.

::

    BlitzError
    ├── APIConnectionError        # request never completed (network / timeout)
    │   └── APITimeoutError
    ├── APIResponseValidationError  # a 2xx body was not valid JSON / not the expected shape
    └── APIStatusError            # a non-2xx HTTP response was received
        ├── AuthenticationError       # 401
        ├── InsufficientRecordsError  # 402
        ├── NotFoundError             # 404
        ├── RateLimitError            # 429 (after retries are exhausted)
        └── ServerError               # 5xx (after retries are exhausted)

Catch :class:`BlitzError` to handle anything this SDK raises.

``InsufficientCreditsError`` remains available as a deprecated alias of
:class:`InsufficientRecordsError`; it is scheduled for removal in 3.0.0.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from pydantic import ValidationError

from .types._models import FairUsage

if TYPE_CHECKING:
    import httpx
    from typing_extensions import deprecated


def _parse_fair_usage(body: Any) -> FairUsage | None:
    """Pull the ``fair_usage`` block out of an error body, if the API sent one.

    The API attaches it to ``402`` responses, so a caller who runs out of records can
    read ``next_reset_at`` off the exception. Never raises: a malformed block just
    yields ``None`` rather than masking the original API error.
    """
    if not isinstance(body, dict):
        return None
    raw = cast("dict[str, Any]", body).get("fair_usage")
    if not isinstance(raw, dict):
        return None
    try:
        return FairUsage.model_validate(raw)
    except ValidationError:
        return None


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


class APIResponseValidationError(BlitzError):
    """A 2xx response body could not be parsed into the expected model.

    Raised when the server returns success but the body is not valid JSON (e.g. an
    HTML error page from a proxy, or an empty body) or does not match the response
    model. This keeps a successful-status surprise inside the :class:`BlitzError`
    hierarchy instead of leaking a raw ``json``/``pydantic`` error.

    Attributes:
        response: The underlying :class:`httpx.Response`.
        status_code: The HTTP status code (a 2xx).
        request_id: The value of the ``x-request-id`` response header, if any.
    """

    def __init__(self, message: str, *, response: httpx.Response) -> None:
        super().__init__(message)
        self.message = message
        self.response = response
        self.status_code = response.status_code
        self.request_id = response.headers.get("x-request-id")


class APIStatusError(BlitzError):
    """The API returned a non-success HTTP status code.

    Attributes:
        status_code: The HTTP status code of the response.
        body: The parsed JSON body, or the raw text if it was not JSON.
        message: A human-readable message extracted from the body when present.
        request_id: The value of the ``x-request-id`` response header, if any.
        fair_usage: The :class:`~blitz_api.types.FairUsage` block from the body, when
            the API sent one (it does on ``402``); ``None`` otherwise.
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
        self.fair_usage = _parse_fair_usage(body)


class AuthenticationError(APIStatusError):
    """401 — the API key is missing or invalid."""


class InsufficientRecordsError(APIStatusError):
    """402 — the key is valid but the account is out of records.

    The API attaches the usage block to this response, so :attr:`~APIStatusError.fair_usage`
    tells you when the balance resets (``fair_usage.next_reset_at``).
    """


class NotFoundError(APIStatusError):
    """404 — the API key or resource does not exist."""


class RateLimitError(APIStatusError):
    """429 — too many requests (raised only after retries are exhausted)."""


class ServerError(APIStatusError):
    """5xx — the API failed (raised only after retries are exhausted)."""


# --- Deprecated aliases ------------------------------------------------------

if TYPE_CHECKING:

    @deprecated(
        "InsufficientCreditsError is renamed to InsufficientRecordsError and will be "
        "removed in 3.0.0."
    )
    class InsufficientCreditsError(InsufficientRecordsError):
        """Deprecated alias for :class:`InsufficientRecordsError`."""

else:
    # A true alias, not a subclass: the client raises ``InsufficientRecordsError``, so a
    # subclass here would stop ``except InsufficientCreditsError`` from catching it.
    InsufficientCreditsError = InsufficientRecordsError
