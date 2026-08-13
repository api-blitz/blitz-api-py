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
    EmploymentType,
    Industry,
    JobFunction,
    JobLevel,
    LastFundingType,
    SalesRegion,
    Seniority,
    WorkArrangement,
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
SeniorityValue = Seniority | str
EmploymentTypeValue = EmploymentType | str
WorkArrangementValue = WorkArrangement | str


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

    # Applied on ``search.people`` only; ``search.companies`` ignores it.
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

    city: KeywordFilter
    country_code: list[str]
    continent: list[ContinentValue]
    sales_region: list[SalesRegionValue]


class PeopleFilter(TypedDict, total=False):
    """People search criteria for ``search.people``."""

    linkedin_url: list[str]  # Match specific people by LinkedIn URL (server caps at 50).
    job_title: PeopleJobTitleFilter
    job_function: list[JobFunctionValue]
    job_level: list[JobLevelValue]
    min_connections: int
    location: PeopleLocationFilter
    education: KeywordFilter


class CascadeTier(TypedDict):
    """One tier of a waterfall ICP cascade, tried in order until results are found.

    Only ``include_title`` is required; the server defaults ``location`` to worldwide
    and ``include_headline_search`` to ``False`` when omitted.
    """

    include_title: list[str]
    location: NotRequired[list[str]]
    include_headline_search: NotRequired[bool]
    exclude_title: NotRequired[list[str]]


class SeniorityFilter(TypedDict, total=False):
    """Include/exclude filter over a job's seniority band.

    These are **years-of-experience** bands on the posting (``0-2``, ``2-5``,
    ``5-10``, ``10+``) — unrelated to the people-side ``JobLevel`` (``C-Team``, ``VP``, ...).
    """

    include: list[SeniorityValue]
    exclude: list[SeniorityValue]


class EmploymentTypeFilter(TypedDict, total=False):
    """Include/exclude filter over the employment type a job offers."""

    include: list[EmploymentTypeValue]
    exclude: list[EmploymentTypeValue]


class WorkArrangementFilter(TypedDict, total=False):
    """Include/exclude filter over where the work is performed."""

    include: list[WorkArrangementValue]
    exclude: list[WorkArrangementValue]


class JobLocationFilter(TypedDict, total=False):
    """Location filter for a job posting (the job's location, not the company HQ)."""

    city: KeywordFilter
    country_code: KeywordFilter  # ISO-3166 alpha-2 codes, matched exactly.


class DatePostedFilter(TypedDict):
    """Recency filter restricting results to jobs posted within the last N days."""

    last_days: int  # 1-3650.


class JobFilter(TypedDict, total=False):
    """Job-level search criteria, shared by ``jobs.search`` and ``jobs.company``."""

    title: KeywordFilter
    description: KeywordFilter
    ai_keywords: KeywordFilter  # Broad theme search across title, description, taxonomies.
    field: KeywordFilter  # Professional field or discipline. Free-form — any label.
    seniority: SeniorityFilter
    employment_type: EmploymentTypeFilter
    work_arrangement: WorkArrangementFilter
    location: JobLocationFilter
    date_posted: DatePostedFilter


class TamJobFilter(TypedDict, total=False):
    """Job criteria for ``company.tam_by_jobs`` — the same fields as ``JobFilter`` plus a
    per-company floor.

    Defined as a standalone ``TypedDict`` (this SDK's flat-``TypedDict`` convention, no
    inheritance) so the shared ``JobFilter`` used by ``jobs.search`` / ``jobs.company`` —
    which have no such field — never gains ``min_per_company``.
    """

    title: KeywordFilter
    description: KeywordFilter
    ai_keywords: KeywordFilter  # Broad theme search across title, description, taxonomies.
    field: KeywordFilter  # Professional field or discipline. Free-form — any label.
    seniority: SeniorityFilter
    employment_type: EmploymentTypeFilter
    work_arrangement: WorkArrangementFilter
    location: JobLocationFilter
    date_posted: DatePostedFilter
    # Only include companies with at least this many matching job postings (integer,
    # 0-25; ``0`` = unset). Raises the bar for what counts as a hit when building a TAM.
    min_per_company: int


class CompanySizeFilter(TypedDict, total=False):
    """Include-only filter over the LinkedIn size buckets. The API exposes no ``exclude``."""

    include: list[EmployeeRangeValue]


class JobCompanyHQFilter(TypedDict, total=False):
    """Headquarters-location filter for the company side of a job search."""

    city: KeywordFilter
    state: KeywordFilter
    country_code: KeywordFilter  # ISO-3166 alpha-2 codes, matched exactly.


class JobCompanyFilter(TypedDict, total=False):
    """Company-level firmographic criteria for ``jobs.search``, matched against the
    enriched company record behind each posting.
    """

    # ``True`` = only staffing/recruitment agencies, ``False`` = exclude confirmed
    # agencies. Omit to include both.
    is_agency: bool
    industry: IndustryFilter
    employee_count: RangeFilter
    size: CompanySizeFilter
    keywords: KeywordFilter
    hq: JobCompanyHQFilter
