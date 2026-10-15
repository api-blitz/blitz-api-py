"""The Search resource: ``client.search``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._compat import TimeoutParam
from ..._pagination_async import AsyncCursorPage, AsyncPageNumberPage
from ...types.filters import (
    CascadeTier,
    CompanyFilter,
    ContinentValue,
    JobFunctionValue,
    JobLevelValue,
    PeopleCompanyFilter,
    PeopleFilter,
    SalesRegionValue,
)
from ...types.search import WaterfallIcpResponse
from ...types.shared import Company, Person

if TYPE_CHECKING:
    from ..._client import AsyncBlitzAPI

_PEOPLE = "/v2/search/people"
_COMPANIES = "/v2/search/companies"
_EMPLOYEE_FINDER = "/v2/search/employee-finder"
_WATERFALL = "/v2/search/waterfall-icp-keyword"


class AsyncSearchResource:
    def __init__(self, client: AsyncBlitzAPI) -> None:
        self._client = client

    async def people(
        self,
        *,
        company: PeopleCompanyFilter | None = None,
        people: PeopleFilter | None = None,
        is_recent_hire: bool | None = None,
        include_active_jobs: bool | None = None,
        include_past_jobs: bool | None = None,
        max_results: int | None = None,
        cursor: str | None = None,
        timeout: TimeoutParam = None,
    ) -> AsyncCursorPage[Person]:
        """Search people across many companies, combining company and persona filters.

        ``is_recent_hire=True`` keeps only people with a job that started in the last 90
        days (the job must also match your other job and company filters; a job with no
        start date never matches). It is a top-level argument, not a key of ``people``.

        ``include_active_jobs`` (server default ``True``) and ``include_past_jobs`` (server
        default ``False``) choose which of a person's jobs are searched. Your job and company
        filters must then hold in the **same** job; that job is returned in ``experiences``
        with ``job_is_current`` set, and a person is returned once (a current job is
        preferred to a past one). Setting both to ``False`` is a ``422``.

        Auto-paginates over every matching person when the result is iterated; use
        ``.iter_pages()`` or the ``cursor=`` arg for manual control.
        """
        body = {
            "company": company,
            "people": people,
            "is_recent_hire": is_recent_hire,
            "include_active_jobs": include_active_jobs,
            "include_past_jobs": include_past_jobs,
            "max_results": max_results,
            "cursor": cursor,
        }
        return await self._client._request(
            "POST", _PEOPLE, body=body, cast_to=AsyncCursorPage[Person], timeout=timeout
        )

    async def companies(
        self,
        *,
        company: CompanyFilter | None = None,
        max_results: int | None = None,
        cursor: str | None = None,
        timeout: TimeoutParam = None,
    ) -> AsyncCursorPage[Company]:
        """Find companies matching ICP filters (industry, size, HQ, revenue, ...).

        Auto-paginates over every matching company; use ``.iter_pages()`` or ``cursor=``
        for manual control.
        """
        body = {"company": company, "max_results": max_results, "cursor": cursor}
        return await self._client._request(
            "POST", _COMPANIES, body=body, cast_to=AsyncCursorPage[Company], timeout=timeout
        )

    async def employee_finder(
        self,
        *,
        company_linkedin_url: str,
        country_code: list[str] | None = None,
        continent: list[ContinentValue] | None = None,
        sales_region: list[SalesRegionValue] | None = None,
        job_level: list[JobLevelValue] | None = None,
        job_function: list[JobFunctionValue] | None = None,
        min_connections_count: int | None = None,
        is_recent_hire: bool | None = None,
        max_results: int | None = None,
        page: int | None = None,
        timeout: TimeoutParam = None,
    ) -> AsyncPageNumberPage[Person]:
        """Search employees at a single company, with page-based pagination.

        ``is_recent_hire=True`` keeps only people whose **current** job at the company
        started in the last 90 days (that job must also match ``job_level`` and
        ``job_function``; a job with no start date never matches).

        Auto-paginates over every matching employee; use ``.iter_pages()`` or ``page=``
        for manual control.
        """
        body = {
            "company_linkedin_url": company_linkedin_url,
            "country_code": country_code,
            "continent": continent,
            "sales_region": sales_region,
            "job_level": job_level,
            "job_function": job_function,
            "min_connections_count": min_connections_count,
            "is_recent_hire": is_recent_hire,
            "max_results": max_results,
            "page": page,
        }
        return await self._client._request(
            "POST",
            _EMPLOYEE_FINDER,
            body=body,
            cast_to=AsyncPageNumberPage[Person],
            timeout=timeout,
        )

    async def waterfall_icp(
        self,
        *,
        company_linkedin_url: str,
        cascade: list[CascadeTier],
        profile_min_connections: int | None = None,
        is_recent_hire: bool | None = None,
        include_active_jobs: bool | None = None,
        include_past_jobs: bool | None = None,
        max_results: int | None = None,
        timeout: TimeoutParam = None,
    ) -> WaterfallIcpResponse:
        """Find the best decision-maker at a company via a prioritized cascade.

        ``profile_min_connections`` sets the minimum LinkedIn connections for a match
        (server defaults to ``0`` — i.e. **no** floor — when omitted).

        ``include_active_jobs`` (server default ``True``) and ``include_past_jobs`` (server
        default ``False``) choose which of a person's jobs are searched. Set
        ``include_past_jobs=True`` to find people by a job they held *before* at the company;
        the company and a cascade's title filters must then hold in the **same** job, and that
        job is returned in ``experiences`` with ``job_is_current`` set. A person is returned
        once. Setting both to ``False`` is a ``422``.

        ``is_recent_hire=True`` keeps only people whose job at the company started in the
        last 90 days, in every cascade. It covers whichever jobs the two flags above select
        (current jobs by default) and the job must also match the cascade title filters; a
        job with no start date never matches.
        """
        body = {
            "company_linkedin_url": company_linkedin_url,
            "cascade": cascade,
            "profile_min_connections": profile_min_connections,
            "is_recent_hire": is_recent_hire,
            "include_active_jobs": include_active_jobs,
            "include_past_jobs": include_past_jobs,
            "max_results": max_results,
        }
        return await self._client._request(
            "POST", _WATERFALL, body=body, cast_to=WaterfallIcpResponse, timeout=timeout
        )
