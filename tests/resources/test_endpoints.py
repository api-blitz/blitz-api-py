"""End-to-end resource tests: correct method/path/body out, typed model back."""

from __future__ import annotations

import json
from typing import Any, cast

import httpx
from pytest_httpx import HTTPXMock

from blitz_api import AsyncBlitzAPI, AsyncCursorPage, BlitzAPI, CursorPage, PageNumberPage
from blitz_api.types import (
    CompanyDistributionByCountryResponse,
    CompanyDistributionByDepartmentResponse,
    CompanyEnrichmentResponse,
    CurrentDateResponse,
    EmailEnrichmentResponse,
    Industry,
    JobFunction,
    JobLevel,
    KeyInfo,
    LastFundingType,
    WaterfallIcpResponse,
)
from tests import data
from tests.conftest import TEST_KEY, url


def _client() -> BlitzAPI:
    return BlitzAPI(api_key=TEST_KEY, rate_limit_rps=None)


def _sent_body(httpx_mock: HTTPXMock) -> dict[str, Any]:
    request = httpx_mock.get_request()
    assert request is not None
    return cast("dict[str, Any]", json.loads(request.content))


def test_key_info_get(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=url("/v2/account/key-info"), method="GET", json=data.KEY_INFO)
    result = _client().account.key_info()

    assert isinstance(result, KeyInfo)
    request = httpx_mock.get_request()
    assert request is not None
    assert request.method == "GET"
    assert request.headers["x-api-key"] == TEST_KEY


def test_enrichment_email_post_body(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/enrichment/email"), method="POST", json=data.EMAIL_ENRICHMENT
    )
    result = _client().enrichment.email(person_linkedin_url="https://www.linkedin.com/in/example")

    assert isinstance(result, EmailEnrichmentResponse)
    assert result.email == "antoine@blitz-agency.com"
    assert _sent_body(httpx_mock) == {"person_linkedin_url": "https://www.linkedin.com/in/example"}


def test_company_enrichment(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/enrichment/company"), method="POST", json=data.COMPANY_ENRICHMENT
    )
    result = _client().enrichment.company(
        company_linkedin_url="https://www.linkedin.com/company/google"
    )
    assert isinstance(result, CompanyEnrichmentResponse)
    assert result.company is not None
    assert result.company.name == "Google"


def test_search_people_serializes_enums_and_drops_none(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=url("/v2/search/people"), method="POST", json=data.PEOPLE_SEARCH)
    result = _client().search.people(
        company={"industry": {"include": [Industry.SOFTWARE_DEVELOPMENT]}},
        people={"job_level": [JobLevel.VP], "job_title": {"include": ["Engineer"]}},
        max_results=5,
    )

    assert isinstance(result, CursorPage)
    body = _sent_body(httpx_mock)
    assert body == {
        "company": {"industry": {"include": ["Software Development"]}},
        "people": {"job_level": ["VP"], "job_title": {"include": ["Engineer"]}},
        "max_results": 5,
    }
    assert "cursor" not in body  # None args are omitted


def test_search_people_serializes_funding_and_hq_state_filters(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=url("/v2/search/people"), method="POST", json=data.PEOPLE_SEARCH)
    _client().search.people(
        company={
            "total_funding": {"min": 1000000},
            "last_funding_amount": {"min": 500000, "max": 5000000},
            "last_funding_year": {"min": 2022},
            "last_funding_type": {"include": [LastFundingType.SERIES_A, LastFundingType.SERIES_B]},
            "lead_investors": {"include": ["Sequoia"]},
            "hq": {"state": {"include": ["California"]}, "country_code": ["US"]},
        },
        max_results=5,
    )
    assert _sent_body(httpx_mock) == {
        "company": {
            "total_funding": {"min": 1000000},
            "last_funding_amount": {"min": 500000, "max": 5000000},
            "last_funding_year": {"min": 2022},
            "last_funding_type": {"include": ["Series A", "Series B"]},
            "lead_investors": {"include": ["Sequoia"]},
            "hq": {"state": {"include": ["California"]}, "country_code": ["US"]},
        },
        "max_results": 5,
    }


def test_search_companies(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/search/companies"), method="POST", json=data.COMPANY_SEARCH
    )
    result = _client().search.companies(company={"employee_range": ["1-10"]}, max_results=1)
    assert isinstance(result, CursorPage)
    assert _sent_body(httpx_mock) == {"company": {"employee_range": ["1-10"]}, "max_results": 1}


def test_employee_finder_serializes_enum_lists(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/search/employee-finder"), method="POST", json=data.EMPLOYEE_FINDER
    )
    result = _client().search.employee_finder(
        company_linkedin_url="https://www.linkedin.com/company/openai",
        job_level=[JobLevel.DIRECTOR],
        job_function=[JobFunction.ENGINEERING],
        max_results=1,
    )
    assert isinstance(result, PageNumberPage)
    assert _sent_body(httpx_mock) == {
        "company_linkedin_url": "https://www.linkedin.com/company/openai",
        "job_level": ["Director"],
        "job_function": ["Engineering"],
        "max_results": 1,
    }


def test_waterfall_icp(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/search/waterfall-icp-keyword"), method="POST", json=data.WATERFALL_ICP
    )
    result = _client().search.waterfall_icp(
        company_linkedin_url="https://www.linkedin.com/company/openai",
        cascade=[
            {"include_title": ["CEO"], "location": ["WORLD"], "include_headline_search": False}
        ],
        max_results=5,
    )
    assert isinstance(result, WaterfallIcpResponse)
    body = _sent_body(httpx_mock)
    assert body["cascade"][0]["include_title"] == ["CEO"]


def test_current_date(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/utils/current-date"), method="POST", json=data.CURRENT_DATE
    )
    result = _client().utils.current_date(region="America/New_York")
    assert isinstance(result, CurrentDateResponse)
    assert _sent_body(httpx_mock) == {"region": "America/New_York"}


def test_company_distribution_by_country(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/enrichment/company-distribution-by-country"),
        method="POST",
        json=data.COUNTRY_DISTRIBUTION,
    )
    result = _client().enrichment.company_distribution_by_country(
        company_linkedin_url="https://www.linkedin.com/company/openai"
    )
    assert isinstance(result, CompanyDistributionByCountryResponse)
    assert result.total_employees == 1234
    assert result.distribution[0].country == "US"
    assert result.distribution[-1].country == "unknown"
    assert _sent_body(httpx_mock) == {
        "company_linkedin_url": "https://www.linkedin.com/company/openai"
    }


async def test_async_company_distribution_by_country(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/enrichment/company-distribution-by-country"),
        method="POST",
        json=data.COUNTRY_DISTRIBUTION,
    )
    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        result = await client.enrichment.company_distribution_by_country(
            company_linkedin_url="https://www.linkedin.com/company/openai"
        )
    assert isinstance(result, CompanyDistributionByCountryResponse)
    assert result.distribution[0].count == 900


def test_company_distribution_by_department(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/enrichment/company-distribution-by-department"),
        method="POST",
        json=data.DEPARTMENT_DISTRIBUTION,
    )
    result = _client().enrichment.company_distribution_by_department(
        company_linkedin_url="https://www.linkedin.com/company/openai"
    )
    assert isinstance(result, CompanyDistributionByDepartmentResponse)
    assert result.total_employees == 1234
    assert result.distribution[0].department == "Engineering"
    assert _sent_body(httpx_mock) == {
        "company_linkedin_url": "https://www.linkedin.com/company/openai"
    }


async def test_async_company_distribution_by_department(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/enrichment/company-distribution-by-department"),
        method="POST",
        json=data.DEPARTMENT_DISTRIBUTION,
    )
    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        result = await client.enrichment.company_distribution_by_department(
            company_linkedin_url="https://www.linkedin.com/company/openai"
        )
    assert isinstance(result, CompanyDistributionByDepartmentResponse)
    assert result.distribution[-1].department == "Other"
    assert result.distribution[-1].count == 12


async def test_async_email_enrichment(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/enrichment/email"), method="POST", json=data.EMAIL_ENRICHMENT
    )
    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        result = await client.enrichment.email(
            person_linkedin_url="https://www.linkedin.com/in/example"
        )
    assert isinstance(result, EmailEnrichmentResponse)
    assert result.found is True


async def test_async_search_people(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=url("/v2/search/people"), method="POST", json=data.PEOPLE_SEARCH)
    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        result = await client.search.people(people={"job_level": [JobLevel.C_TEAM]})
    assert isinstance(result, AsyncCursorPage)
    assert result.results[0].full_name == "Beulah Lee"


def test_request_includes_user_agent(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=url("/v2/account/key-info"), method="GET", json=data.KEY_INFO)
    _client().account.key_info()
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["user-agent"].startswith("blitz-api-py/")
    assert isinstance(request, httpx.Request)


def test_per_call_timeout_is_forwarded(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/enrichment/email"), method="POST", json=data.EMAIL_ENRICHMENT
    )
    _client().enrichment.email(
        person_linkedin_url="https://www.linkedin.com/in/example", timeout=12.5
    )
    request = httpx_mock.get_request()
    assert request is not None
    assert request.extensions["timeout"]["read"] == 12.5


def test_default_timeout_is_used_without_override(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=url("/v2/account/key-info"), method="GET", json=data.KEY_INFO)
    _client().account.key_info()
    request = httpx_mock.get_request()
    assert request is not None
    assert request.extensions["timeout"]["read"] == 30.0  # DEFAULT_TIMEOUT
