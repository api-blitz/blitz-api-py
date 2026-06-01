"""The Search resource: ``client.search``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..types.filters import (
    CascadeTier,
    CompanyFilter,
    ContinentValue,
    JobFunctionValue,
    JobLevelValue,
    PeopleFilter,
    SalesRegionValue,
)
from ..types.search import (
    CompanySearchResponse,
    EmployeeFinderResponse,
    PeopleSearchResponse,
    WaterfallIcpResponse,
)

if TYPE_CHECKING:
    from .._client import AsyncBlitzAPI, BlitzAPI

_PEOPLE = "/v2/search/people"
_COMPANIES = "/v2/search/companies"
_EMPLOYEE_FINDER = "/v2/search/employee-finder"
_WATERFALL = "/v2/search/waterfall-icp-keyword"


def _drop_none(**kwargs: Any) -> dict[str, Any]:
    """Build a request body keeping only the arguments the caller provided."""
    return {key: value for key, value in kwargs.items() if value is not None}


def _employee_finder_body(
    *,
    company_linkedin_url: str,
    country_code: list[str] | None,
    continent: list[ContinentValue] | None,
    sales_region: list[SalesRegionValue] | None,
    job_level: list[JobLevelValue] | None,
    job_function: list[JobFunctionValue] | None,
    min_connections_count: int | None,
    max_results: int | None,
    page: int | None,
) -> dict[str, Any]:
    return _drop_none(
        company_linkedin_url=company_linkedin_url,
        country_code=country_code,
        continent=continent,
        sales_region=sales_region,
        job_level=job_level,
        job_function=job_function,
        min_connections_count=min_connections_count,
        max_results=max_results,
        page=page,
    )


class SearchResource:
    def __init__(self, client: BlitzAPI) -> None:
        self._client = client

    def people(
        self,
        *,
        company: CompanyFilter | None = None,
        people: PeopleFilter | None = None,
        max_results: int | None = None,
        cursor: str | None = None,
    ) -> PeopleSearchResponse:
        """Search people across many companies, combining company and persona filters."""
        body = _drop_none(company=company, people=people, max_results=max_results, cursor=cursor)
        return self._client._request("POST", _PEOPLE, body=body, cast_to=PeopleSearchResponse)

    def companies(
        self,
        *,
        company: CompanyFilter | None = None,
        max_results: int | None = None,
        cursor: str | None = None,
    ) -> CompanySearchResponse:
        """Find companies matching ICP filters (industry, size, HQ, revenue, ...)."""
        body = _drop_none(company=company, max_results=max_results, cursor=cursor)
        return self._client._request("POST", _COMPANIES, body=body, cast_to=CompanySearchResponse)

    def employee_finder(
        self,
        *,
        company_linkedin_url: str,
        country_code: list[str] | None = None,
        continent: list[ContinentValue] | None = None,
        sales_region: list[SalesRegionValue] | None = None,
        job_level: list[JobLevelValue] | None = None,
        job_function: list[JobFunctionValue] | None = None,
        min_connections_count: int | None = None,
        max_results: int | None = None,
        page: int | None = None,
    ) -> EmployeeFinderResponse:
        """Search employees at a single company, with page-based pagination."""
        body = _employee_finder_body(
            company_linkedin_url=company_linkedin_url,
            country_code=country_code,
            continent=continent,
            sales_region=sales_region,
            job_level=job_level,
            job_function=job_function,
            min_connections_count=min_connections_count,
            max_results=max_results,
            page=page,
        )
        return self._client._request(
            "POST", _EMPLOYEE_FINDER, body=body, cast_to=EmployeeFinderResponse
        )

    def waterfall_icp(
        self,
        *,
        company_linkedin_url: str,
        cascade: list[CascadeTier],
        max_results: int | None = None,
    ) -> WaterfallIcpResponse:
        """Find the best decision-maker at a company via a prioritized cascade."""
        body = _drop_none(
            company_linkedin_url=company_linkedin_url, cascade=cascade, max_results=max_results
        )
        return self._client._request("POST", _WATERFALL, body=body, cast_to=WaterfallIcpResponse)


class AsyncSearchResource:
    def __init__(self, client: AsyncBlitzAPI) -> None:
        self._client = client

    async def people(
        self,
        *,
        company: CompanyFilter | None = None,
        people: PeopleFilter | None = None,
        max_results: int | None = None,
        cursor: str | None = None,
    ) -> PeopleSearchResponse:
        """Search people across many companies, combining company and persona filters."""
        body = _drop_none(company=company, people=people, max_results=max_results, cursor=cursor)
        return await self._client._request("POST", _PEOPLE, body=body, cast_to=PeopleSearchResponse)

    async def companies(
        self,
        *,
        company: CompanyFilter | None = None,
        max_results: int | None = None,
        cursor: str | None = None,
    ) -> CompanySearchResponse:
        """Find companies matching ICP filters (industry, size, HQ, revenue, ...)."""
        body = _drop_none(company=company, max_results=max_results, cursor=cursor)
        return await self._client._request(
            "POST", _COMPANIES, body=body, cast_to=CompanySearchResponse
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
        max_results: int | None = None,
        page: int | None = None,
    ) -> EmployeeFinderResponse:
        """Search employees at a single company, with page-based pagination."""
        body = _employee_finder_body(
            company_linkedin_url=company_linkedin_url,
            country_code=country_code,
            continent=continent,
            sales_region=sales_region,
            job_level=job_level,
            job_function=job_function,
            min_connections_count=min_connections_count,
            max_results=max_results,
            page=page,
        )
        return await self._client._request(
            "POST", _EMPLOYEE_FINDER, body=body, cast_to=EmployeeFinderResponse
        )

    async def waterfall_icp(
        self,
        *,
        company_linkedin_url: str,
        cascade: list[CascadeTier],
        max_results: int | None = None,
    ) -> WaterfallIcpResponse:
        """Find the best decision-maker at a company via a prioritized cascade."""
        body = _drop_none(
            company_linkedin_url=company_linkedin_url, cascade=cascade, max_results=max_results
        )
        return await self._client._request(
            "POST", _WATERFALL, body=body, cast_to=WaterfallIcpResponse
        )
