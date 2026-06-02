"""Namespaced API resources, grouped by the Blitz API's OpenAPI tags.

The ``Async*`` classes are hand-written in ``resources/_async``; the sync classes in
``resources/_sync`` are generated from them by ``scripts/gen_sync.py``.
"""

from __future__ import annotations

from ._async.account import AsyncAccountResource
from ._async.enrichment import AsyncEnrichmentResource
from ._async.search import AsyncSearchResource
from ._async.utils import AsyncUtilsResource
from ._sync.account import AccountResource
from ._sync.enrichment import EnrichmentResource
from ._sync.search import SearchResource
from ._sync.utils import UtilsResource

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
