"""Typed Python SDK for the Blitz API.

Quickstart::

    from blitz_api import BlitzAPI

    client = BlitzAPI()  # reads the BLITZ_API_KEY environment variable
    result = client.enrichment.email(
        person_linkedin_url="https://www.linkedin.com/in/example",
    )
    print(result.found, result.email)

See https://docs.blitz-api.ai for the full API reference.
"""

from __future__ import annotations

from ._client import AsyncBlitzAPI, BlitzAPI
from ._exceptions import (
    APIConnectionError,
    APIResponseValidationError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BlitzError,
    InsufficientCreditsError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from ._pagination_async import AsyncCursorPage, AsyncPageNumberPage
from ._pagination_sync import CursorPage, PageNumberPage
from ._version import __version__
from .types import (
    CompanyFilter,
    Industry,
    PeopleFilter,
)

__all__ = [
    "__version__",
    # clients
    "BlitzAPI",
    "AsyncBlitzAPI",
    # pagination (returned by the search.* methods)
    "CursorPage",
    "AsyncCursorPage",
    "PageNumberPage",
    "AsyncPageNumberPage",
    # exceptions
    "BlitzError",
    "APIConnectionError",
    "APITimeoutError",
    "APIResponseValidationError",
    "APIStatusError",
    "AuthenticationError",
    "InsufficientCreditsError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    # commonly-used types (full set under blitz_api.types)
    "Industry",
    "CompanyFilter",
    "PeopleFilter",
]
