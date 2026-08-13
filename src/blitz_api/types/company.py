"""Response models for the Company resource (TAM builders).

``company.tam_by_jobs`` returns ``CursorPage[TamByJobsMatch]`` (the auto-paging cursor
page defined in :mod:`blitz_api._pagination_async` / ``_pagination_sync``), so there is
no per-endpoint response wrapper here — only the ``TamByJobsMatch`` item model.
"""

from __future__ import annotations

from ._models import BlitzModel
from .shared import Company

__all__ = [
    "TamByJobsMatch",
]


class TamByJobsMatch(BlitzModel):
    """One ``company.tam_by_jobs`` match: a company plus how many of its live job
    postings matched the filters.

    ``matched_jobs`` is the count on this company (it respects the request's
    ``job.min_per_company`` floor). ``company`` reuses the shared
    :class:`~blitz_api.types.shared.Company` model.

    Unlike the search/jobs cursor pages, the TAM cursor page carries **no**
    ``total_results`` (the spec omits it); iterate until ``cursor`` is ``None``.
    """

    company: Company | None = None
    matched_jobs: int | None = None
