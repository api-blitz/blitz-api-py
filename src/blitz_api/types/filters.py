"""Typed request structures (``TypedDict``) for the search endpoints.

These give call-site autocomplete and static checking for the nested filter
objects accepted by ``search.people`` and ``search.companies``. Enum-constrained
fields accept either an enum member (autocompleted, e.g. ``Industry.BANKING``) or
a raw string, so power users are never blocked.

All keys are optional unless noted; omit a filter to leave it unset.
"""

from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from .enums import (
    CompanyType,
    Continent,
    EmployeeRange,
    Industry,
    JobFunction,
    JobLevel,
    LastFundingType,
    SalesRegion,
)

# Each accepts an enum member (autocompleted) or a raw string, so callers are
# never blocked by a value missing from the vendored taxonomy. Note: because the
# enums subclass ``str``, ``Enum | str`` collapses to ``str`` for the type checker, so
# the taxonomy is an autocomplete aid, not a statically enforced constraint — a typo'd
# value is sent as-is and rejected (or ignored) by the API rather than caught by mypy.
IndustryValue = Industry | str
CompanyTypeValue = CompanyType | str
EmployeeRangeValue = EmployeeRange | str
LastFundingTypeValue = LastFundingType | str
ContinentValue = Continent | str
SalesRegionValue = SalesRegion | str
JobFunctionValue = JobFunction | str
JobLevelValue = JobLevel | str


class KeywordFilter(TypedDict, total=False):
    """Free-text include/exclude keyword filter."""

    include: list[str]
    exclude: list[str]


class IndustryFilter(TypedDict, total=False):
    """Include/exclude filter over the fixed industry taxonomy."""

    include: list[IndustryValue]
    exclude: list[IndustryValue]


class CompanyTypeFilter(TypedDict, total=False):
    """Include/exclude filter over company types."""

    include: list[CompanyTypeValue]
    exclude: list[CompanyTypeValue]


class LastFundingTypeFilter(TypedDict, total=False):
    """Include/exclude filter over the last funding round type."""

    include: list[LastFundingTypeValue]
    exclude: list[LastFundingTypeValue]


class RangeFilter(TypedDict, total=False):
    """Numeric range filter. ``0`` means unset for most fields."""

    min: float
    max: float


class CompanyHQFilter(TypedDict, total=False):
    """Headquarters-location filter for company search."""

    city: KeywordFilter
    state: KeywordFilter
    country_code: list[str]
    continent: list[ContinentValue]
    sales_region: list[SalesRegionValue]


class CompanyFilter(TypedDict, total=False):
    """Company search criteria, shared by ``search.companies`` and ``search.people``."""

    linkedin_url: list[str]
    name: KeywordFilter
    industry: IndustryFilter
    type: CompanyTypeFilter
    employee_range: list[EmployeeRangeValue]
    employee_count: RangeFilter
    min_linkedin_followers: int
    revenue: RangeFilter
    naics_code: KeywordFilter
    sic_code: KeywordFilter
    web_traffic: RangeFilter
    ad_spend: RangeFilter
    total_funding: RangeFilter
    last_funding_amount: RangeFilter
    last_funding_year: RangeFilter
    last_funding_type: LastFundingTypeFilter
    lead_investors: KeywordFilter
    keywords: KeywordFilter
    founded_year: RangeFilter
    hq: CompanyHQFilter


class PeopleJobTitleFilter(TypedDict, total=False):
    """Job-title filter. Wrap a value in ``[brackets]`` for an exact match."""

    include_linkedin_headline: bool
    include: list[str]
    exclude: list[str]


class PeopleLocationFilter(TypedDict, total=False):
    """Location filter for the people side of a people search."""

    city: list[str]
    country_code: list[str]
    continent: list[ContinentValue]
    sales_region: list[SalesRegionValue]


class PeopleFilter(TypedDict, total=False):
    """People search criteria for ``search.people``."""

    job_title: PeopleJobTitleFilter
    job_function: list[JobFunctionValue]
    job_level: list[JobLevelValue]
    min_connections: int
    location: PeopleLocationFilter
    education: KeywordFilter


class CascadeTier(TypedDict):
    """One tier of a waterfall ICP cascade, tried in order until results are found."""

    include_title: list[str]
    location: list[str]
    include_headline_search: bool
    exclude_title: NotRequired[list[str]]
