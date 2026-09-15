"""Response models for the Company resource (TAM builders).

``company.tam_by_jobs`` / ``company.tam_by_people`` return ``CursorPage[...]`` (the
auto-paging cursor page defined in :mod:`blitz_api._pagination_async` /
``_pagination_sync``), so there is no per-endpoint response wrapper here — only the
match item models.
"""

from __future__ import annotations

from ._models import BlitzModel
from .shared import Company

__all__ = [
    "TamByJobsMatch",
    "TamByPeopleMatch",
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


class TamByPeopleMatch(BlitzModel):
    """One ``company.tam_by_people`` match: a company plus how many of its current
    employees matched the filters.

    ``matched_people`` is the count on this company (it respects the request's
    ``people.min_per_company`` floor). ``company`` reuses the shared
    :class:`~blitz_api.types.shared.Company` model.

    Like the TAM-by-jobs page, this cursor page carries **no** ``total_results``;
    iterate until ``cursor`` is ``None``.
    """

    company: Company | None = None
    matched_people: int | None = None
