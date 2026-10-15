"""Typed request structures (``TypedDict``) for the search endpoints.

These give call-site autocomplete and static checking for the nested filter
objects accepted by ``search.people`` and ``search.companies``. Enum-constrained
fields accept either an enum member (autocompleted, e.g. ``Industry.BANKING``) or
a raw string, so power users are never blocked.

All keys are optional unless noted; omit a filter to leave it unset. The search
endpoints cap every filter list at **50 entries** — a longer list is rejected with a
``422``, so split a bigger inclusion/exclusion set across several requests.
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
    MxProvider,
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
MxProviderValue = MxProvider | str
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
    """Include/exclude filter over the fixed industry taxonomy.

    :attr:`~blitz_api.types.Industry.UNKNOWN` (``"Unknown"``) is a bucket, not a real
    industry. In ``include`` it is added to the industries you list (``["Banking",
    "Unknown"]`` returns banks *plus* the bucket); in ``exclude`` it drops them. Before it
    existed, reaching those records meant listing every other industry in ``exclude``,
    which the 50-entry cap made impossible.

    **What lands in the bucket depends on the endpoint** (widened 2026-09-17):

    * ``search.companies`` — companies with no industry on file.
    * ``search.people`` / ``company.tam_by_people`` — the above, **plus people with no
      company attached at all**.
    * ``jobs.search`` / ``company.tam_by_jobs`` (via :class:`JobCompanyFilter`) — the
      above, **plus job postings with no company attached at all**.
    """

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


class MxProviderFilter(TypedDict, total=False):
    """Include/exclude filter over the mail provider behind a company's domains.

    :attr:`~blitz_api.types.MxProvider.ANY` (``"any"``) stands for *every* provider. In
    ``include`` it keeps companies that have MX data at all; in ``exclude`` it keeps
    companies that have **none**. So ``{"include": ["any"], "exclude": ["google"]}`` means
    "has MX data, but not on Google".
    """

    include: list[MxProviderValue]
    exclude: list[MxProviderValue]


class MxFilter(TypedDict, total=False):
    """Mail-provider criteria, read from the MX records of a company's domains.

    A company matches when **any** of its domains uses the provider. A company with no MX
    data is never matched by ``include`` and never dropped by ``exclude`` — unless you use
    :attr:`~blitz_api.types.MxProvider.ANY`.
    """

    provider: MxProviderFilter


class RangeFilter(TypedDict, total=False):
    """Numeric range filter. ``0`` means unset for most fields.

    A ``max`` of ``0`` still means *no upper bound*, but since 2026-09-16 a range whose
    ``min`` is genuinely above its ``max`` is rejected with a ``422`` naming the field
    (it used to be accepted, returning no results — or a ``500`` on ``company.revenue``).
    Not pre-validated here, in line with the rest of the filter surface.
    """

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
    """Company search criteria, shared by ``search.companies``, ``search.people`` and
    ``company.tam_by_people``.

    ``linkedin_url`` is deliberately **not** here: only the people-side endpoints honour
    it, and ``search.companies`` accepts-then-ignores it. See :class:`PeopleCompanyFilter`.
    """

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
    mx: MxFilter


class PeopleCompanyFilter(CompanyFilter, total=False):
    """Company criteria for the people-side searches — every :class:`CompanyFilter` field
    plus the ``linkedin_url`` filter that only ``search.people`` and
    ``company.tam_by_people`` honour.

    Extending, rather than leaving ``linkedin_url`` on the shared filter, keeps it off
    ``search.companies``: the live spec declares it on the ``company`` object of
    ``/v2/search/people`` and ``/v2/company/tam-by-people`` but **not**
    ``/v2/search/companies``, and request schemas are open (no ``additionalProperties:
    false``), so that endpoint accepts the key and silently returns results for your other
    criteria. That is the same accepted-but-ignored failure mode that got ``linkedin_url``
    removed from :class:`PeopleFilter`, and the same split as :class:`TamPeopleFilter` over
    :class:`PeopleFilter`.

    The assignability caveat on :class:`TamJobFilter` applies verbatim: this only rejects a
    ``search.companies`` call site that passes a *dict literal* carrying ``linkedin_url``.
    A **declared** ``PeopleCompanyFilter`` variable is still accepted there, because
    ``TypedDict`` assignability is structural.
    """

    # Match specific companies by LinkedIn URL. Capped at 50 entries like every other
    # filter list.
    linkedin_url: list[str]


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


class PeopleEducationFilter(KeywordFilter, total=False):
    """Education filter for the person: phrase include/exclude plus start/end year ranges.

    ``start_year`` and ``end_year`` (graduation year) are :class:`RangeFilter` bounds with
    ``0`` meaning unset. They apply to the **same education entry** that ``include`` matches,
    so the school and the year are correlated rather than matched independently. An entry
    with no such year never matches a bound.
    """

    start_year: RangeFilter
    end_year: RangeFilter


class PeopleFilter(TypedDict, total=False):
    """People search criteria for ``search.people``.

    ``linkedin_url`` is deliberately absent: ``/v2/search/people`` stopped honouring it
    on 2026-09-11 (the request still succeeds, but the filter is *ignored*, so you get
    results for your other criteria instead of the people you asked for). Match specific
    people by LinkedIn URL with ``company.tam_by_people`` (:class:`TamPeopleFilter`),
    which still accepts it.

    This is the persona criteria ``search.people`` and ``company.tam_by_people`` share;
    :class:`SearchPeopleFilter` adds the past-job flags only ``search.people`` takes, and
    :class:`TamPeopleFilter` adds the keys only ``company.tam_by_people`` takes.

    ``is_recent_hire`` is a key of *this* object, not a top-level argument of either method.
    (Not every route is the same: ``search.employee_finder`` and the two
    ``enrichment.company_distribution_by_*`` methods take it as a top-level argument.) The
    API rejects unknown fields at any depth with a ``422``, so a flag in the wrong place
    fails the call.
    """

    job_title: PeopleJobTitleFilter
    job_function: list[JobFunctionValue]
    job_level: list[JobLevelValue]
    min_connections: int
    location: PeopleLocationFilter
    # ``| KeywordFilter`` is deliberate: this field was a ``KeywordFilter`` before it gained
    # year ranges, and a ``KeywordFilter`` *variable* is not assignable to the wider
    # ``PeopleEducationFilter`` alone (its extra optional keys could hold any type). The union
    # keeps that existing usage compiling; dict literals and ``PeopleEducationFilter`` variables
    # are unaffected.
    education: PeopleEducationFilter | KeywordFilter
    # Only people with a job that started in the last 90 days. The job must also match the
    # other job and company filters; a job with no start date never matches. On
    # ``search.people`` it covers the jobs ``include_active_jobs`` / ``include_past_jobs``
    # select (current jobs by default); on ``company.tam_by_people``, current jobs.
    is_recent_hire: bool


class SearchPeopleFilter(PeopleFilter, total=False):
    """People criteria for ``search.people`` — every :class:`PeopleFilter` field plus the
    flags that choose which of a person's jobs are searched.

    ``company.tam_by_people`` does **not** take these two (its ``people`` object has only
    ``is_recent_hire`` of the job-scope flags), which is why they are not on
    :class:`PeopleFilter`. ``search.people`` accepts ``SearchPeopleFilter | PeopleFilter`` so
    an existing ``PeopleFilter`` variable keeps type-checking: a ``PeopleFilter`` variable is
    not assignable to this wider type alone (``TypedDict`` assignability is structural, and
    the extra optional keys could hold anything).
    """

    # Search the current jobs of each person (server default ``True``). Your job and company
    # filters must hold in the *same* job; that job is returned in ``experiences`` with
    # ``job_is_current`` set.
    include_active_jobs: bool
    # Also search the past jobs of each person (server default ``False``). A person is returned
    # once, with the matched job; a current job is preferred to a past one. Setting both
    # ``include_*_jobs`` flags to ``False`` is a ``422``.
    include_past_jobs: bool


class CascadeTier(TypedDict):
    """One tier of a waterfall ICP cascade, tried in order until results are found.

    Only ``include_title`` is required; the server defaults ``location`` to worldwide
    and ``include_headline_search`` to ``False`` when omitted. The ``cascade`` list is
    capped at **10 tiers**, and each tier at 50 title phrases.

    ``is_recent_hire``, ``include_active_jobs`` and ``include_past_jobs`` are per-tier keys,
    not arguments of ``search.waterfall_icp``: each tier can scope its own search, so a
    cascade can try recent hires first and fall back to everyone.
    """

    include_title: list[str]
    location: NotRequired[list[str]]
    include_headline_search: NotRequired[bool]
    exclude_title: NotRequired[list[str]]
    # Only people whose job at the company started in the last 90 days. It covers the jobs
    # this tier's ``include_active_jobs`` / ``include_past_jobs`` select (current jobs by
    # default), and that job must also match the tier's title filters; a job with no start
    # date never matches.
    is_recent_hire: NotRequired[bool]
    # Search the current jobs of each person (server default ``True``). The company and the
    # tier's title filters must hold in the same job; it is returned in ``experiences`` with
    # ``job_is_current`` set.
    include_active_jobs: NotRequired[bool]
    # Also search the jobs a person held *before* at the company (server default ``False``).
    # A person is returned once. Both ``include_*_jobs`` flags ``False`` is a ``422``.
    include_past_jobs: NotRequired[bool]


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

    # Wrap a phrase in ``[brackets]`` (e.g. ``"[Head of Sales]"``) to match the whole title
    # exactly, ignoring case and accents; an unbracketed phrase is a tokenized full-text match.
    title: KeywordFilter
    description: KeywordFilter
    ai_keywords: KeywordFilter  # Broad theme search across title, description, taxonomies.
    field: KeywordFilter  # Professional field or discipline. Free-form — any label.
    seniority: SeniorityFilter
    employment_type: EmploymentTypeFilter
    work_arrangement: WorkArrangementFilter
    location: JobLocationFilter
    date_posted: DatePostedFilter


class TamJobFilter(JobFilter, total=False):
    """Job criteria for ``company.tam_by_jobs`` — every ``JobFilter`` field plus a
    per-company floor.

    Extends ``JobFilter`` rather than restating it, so the shared job criteria can never
    drift between the two. Inheriting cannot add ``min_per_company`` to ``JobFilter``
    itself, so a ``jobs.search`` / ``jobs.company`` call site that passes a *dict literal*
    carrying it is still rejected. A **declared** ``TamJobFilter`` variable is accepted
    there either way — TypedDict assignability is structural, so the older flat copy never
    bought that protection either. See ``docs/CONTEXT.md`` §5 for the measurement.
    """

    # Only include companies with at least this many matching job postings (integer,
    # 0-25; ``0`` = unset). Raises the bar for what counts as a hit when building a TAM.
    min_per_company: int


class TamPeopleFilter(PeopleFilter, total=False):
    """People criteria for ``company.tam_by_people`` — every :class:`PeopleFilter` field
    plus ``linkedin_url`` and a per-company floor.

    Extends ``PeopleFilter`` for the same reason as :class:`TamJobFilter`, and because
    the API documents this endpoint as taking the same persona input as Find People: sharing
    the base is what keeps that true as the persona filters evolve. The one deliberate gap is
    :class:`SearchPeopleFilter`'s ``include_active_jobs`` / ``include_past_jobs``, which only
    ``search.people`` takes.
    """

    # Match specific people by LinkedIn URL. Still honoured here (unlike on
    # ``search.people``). Capped at 50 entries like every other filter list.
    linkedin_url: list[str]
    # Only return companies with at least this many matching current employees (integer,
    # 0-25; ``0`` = unset). When it filters heavily a page may come back partial — keep
    # paging until ``cursor`` is ``None``.
    min_per_company: int


class CompanySizeFilter(TypedDict, total=False):
    """Include-only filter over the LinkedIn size buckets. The API exposes no ``exclude``."""

    include: list[EmployeeRangeValue]


class JobCompanyHQFilter(TypedDict, total=False):
    """Headquarters-location filter for the company side of a job search.

    ``city`` and ``state`` take the same ``[brackets]`` exact-match syntax as
    :attr:`JobFilter.title`: ``"[San Francisco]"`` matches the whole value exactly (ignoring
    case and accents), while an unbracketed phrase is a tokenized full-text match.
    """

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
