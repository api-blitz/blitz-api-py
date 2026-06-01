"""Response models for the Search resource."""

from __future__ import annotations

from ._models import BlitzModel
from .shared import Company, Person

__all__ = [
    "PeopleSearchResponse",
    "CompanySearchResponse",
    "EmployeeFinderResponse",
    "WaterfallIcpMatch",
    "WaterfallIcpResponse",
]


class PeopleSearchResponse(BlitzModel):
    """Cursor-paginated result of ``search.people``."""

    total_results: int | None = None
    results: list[Person] = []
    results_length: int | None = None
    max_results: int | None = None
    cursor: str | None = None


class CompanySearchResponse(BlitzModel):
    """Cursor-paginated result of ``search.companies``."""

    total_results: int | None = None
    results: list[Company] = []
    results_length: int | None = None
    max_results: int | None = None
    cursor: str | None = None


class EmployeeFinderResponse(BlitzModel):
    """Page-paginated result of ``search.employee_finder``."""

    company_linkedin_url: str | None = None
    max_results: int | None = None
    results_length: int | None = None
    page: int | None = None
    total_pages: int | None = None
    results: list[Person] = []


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

    results: list[WaterfallIcpMatch] = []
