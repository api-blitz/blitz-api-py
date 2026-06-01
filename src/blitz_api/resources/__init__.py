"""Namespaced API resources, grouped by the Blitz API's OpenAPI tags."""

from __future__ import annotations

from .account import AccountResource, AsyncAccountResource
from .enrichment import AsyncEnrichmentResource, EnrichmentResource
from .search import AsyncSearchResource, SearchResource
from .utils import AsyncUtilsResource, UtilsResource

__all__ = [
    "AccountResource",
    "AsyncAccountResource",
    "SearchResource",
    "AsyncSearchResource",
    "EnrichmentResource",
    "AsyncEnrichmentResource",
    "UtilsResource",
    "AsyncUtilsResource",
]
