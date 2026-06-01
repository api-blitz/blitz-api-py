"""End-to-end resource tests: correct method/path/body out, typed model back."""

from __future__ import annotations

import json
from typing import Any, cast

import httpx
from pytest_httpx import HTTPXMock

from blitz_api import AsyncBlitzAPI, BlitzAPI
from blitz_api.types import (
    CompanyEnrichmentResponse,
    CompanySearchResponse,
    CurrentDateResponse,
    EmailEnrichmentResponse,
    EmployeeFinderResponse,
    Industry,
    JobFunction,
    JobLevel,
    KeyInfo,
    PeopleSearchResponse,
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

    assert isinstance(result, PeopleSearchResponse)
    body = _sent_body(httpx_mock)
    assert body == {
        "company": {"industry": {"include": ["Software Development"]}},
        "people": {"job_level": ["VP"], "job_title": {"include": ["Engineer"]}},
        "max_results": 5,
    }
    assert "cursor" not in body  # None args are omitted


def test_search_companies(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/search/companies"), method="POST", json=data.COMPANY_SEARCH
    )
    result = _client().search.companies(company={"employee_range": ["1-10"]}, max_results=1)
    assert isinstance(result, CompanySearchResponse)
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
    assert isinstance(result, EmployeeFinderResponse)
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
    assert isinstance(result, PeopleSearchResponse)
    assert result.results[0].full_name == "Beulah Lee"


def test_request_includes_user_agent(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=url("/v2/account/key-info"), method="GET", json=data.KEY_INFO)
    _client().account.key_info()
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["user-agent"].startswith("blitz-api-py/")
    assert isinstance(request, httpx.Request)
