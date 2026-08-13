"""Namespaced API resources, grouped by the Blitz API's OpenAPI tags.

The ``Async*`` classes are hand-written in ``resources/_async``; the sync classes in
``resources/_sync`` are generated from them by ``scripts/gen_sync.py``.
"""

from __future__ import annotations

from ._async.account import AsyncAccountResource
from ._async.changelog import AsyncChangelogResource
from ._async.company import AsyncCompanyResource
from ._async.enrichment import AsyncEnrichmentResource
from ._async.jobs import AsyncJobsResource
from ._async.search import AsyncSearchResource
from ._async.utils import AsyncUtilsResource
from ._sync.account import AccountResource
from ._sync.changelog import ChangelogResource
from ._sync.company import CompanyResource
from ._sync.enrichment import EnrichmentResource
from ._sync.jobs import JobsResource
from ._sync.search import SearchResource
from ._sync.utils import UtilsResource

__all__ = [
    "AccountResource",
    "AsyncAccountResource",
    "SearchResource",
    "AsyncSearchResource",
    "JobsResource",
    "AsyncJobsResource",
    "CompanyResource",
    "AsyncCompanyResource",
    "EnrichmentResource",
    "AsyncEnrichmentResource",
    "UtilsResource",
    "AsyncUtilsResource",
    "ChangelogResource",
    "AsyncChangelogResource",
]
