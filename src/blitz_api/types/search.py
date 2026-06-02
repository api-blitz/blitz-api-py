"""Response models for the Search resource.

``search.people``/``search.companies`` return ``CursorPage[...]`` and
``search.employee_finder`` returns ``PageNumberPage[...]`` (auto-paging page objects
defined in :mod:`blitz_api._pagination_async` / ``_pagination_sync``), so those
per-endpoint response models no longer live here. Only the non-paginated waterfall
result does.
"""

from __future__ import annotations

from ._models import BlitzModel
from .shared import Person

__all__ = [
    "WaterfallIcpMatch",
    "WaterfallIcpResponse",
]


class WaterfallIcpMatch(BlitzModel):
    """A single match from a waterfall ICP search.

    ``icp`` is the cascade tier that matched (1 = highest priority) and
    ``ranking`` is the overall relevance within the company (1 = most relevant).
    """

    icp: int | None = None
    ranking: int | None = None
    person: Person | None = None


class WaterfallIcpResponse(BlitzModel):
    """Result of ``search.waterfall_icp``."""

    company_linkedin_url: str | None = None
    max_results: int | None = None
    results_length: int | None = None
    results: list[WaterfallIcpMatch] = []
