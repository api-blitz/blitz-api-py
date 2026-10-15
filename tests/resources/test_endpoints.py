"""End-to-end resource tests: correct method/path/body out, typed model back."""

from __future__ import annotations

import json
from typing import Any, cast

import httpx
from pytest_httpx import HTTPXMock

from blitz_api import AsyncBlitzAPI, AsyncCursorPage, BlitzAPI, CursorPage, PageNumberPage
from blitz_api.types import (
    ChangelogEntry,
    CompanyDistributionByCountryResponse,
    CompanyDistributionByDepartmentResponse,
    CompanyEnrichmentResponse,
    CurrentDateResponse,
    EmailEnrichmentResponse,
    EmploymentType,
    Industry,
    JobFunction,
    JobLevel,
    KeyInfo,
    LastFundingType,
    MxProvider,
    PeopleFilter,
    PersonEnrichmentResponse,
    SearchPeopleFilter,
    Seniority,
    TamPeopleFilter,
    WaterfallIcpResponse,
    WorkArrangement,
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
    assert result.records_remaining == 99.5
    request = httpx_mock.get_request()
    assert request is not None
    assert request.method == "GET"
    assert request.headers["x-api-key"] == TEST_KEY


def test_enrichment_person_post_body(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/enrichment/person"), method="POST", json=data.PERSON_ENRICHMENT
    )
    result = _client().enrichment.person(person_linkedin_url="https://www.linkedin.com/in/example")

    assert isinstance(result, PersonEnrichmentResponse)
    assert result.found is True
    assert result.person is not None
    assert result.person.full_name == "Beulah Lee"
    # The whole career, not just the current position.
    assert len(result.person.experiences) == 2
    assert _sent_body(httpx_mock) == {"person_linkedin_url": "https://www.linkedin.com/in/example"}


async def test_async_enrichment_person(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/enrichment/person"), method="POST", json=data.PERSON_ENRICHMENT
    )
    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        result = await client.enrichment.person(
            person_linkedin_url="https://www.linkedin.com/in/example"
        )
    assert isinstance(result, PersonEnrichmentResponse)
    assert result.person is not None
    assert result.person.full_name == "Beulah Lee"


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
        people={
            "job_level": [JobLevel.VP],
            "job_title": {"include": ["Engineer"]},
            "min_connections": 200,
        },
        max_results=5,
    )

    assert isinstance(result, CursorPage)
    body = _sent_body(httpx_mock)
    assert body == {
        "company": {"industry": {"include": ["Software Development"]}},
        "people": {
            "job_level": ["VP"],
            "job_title": {"include": ["Engineer"]},
            "min_connections": 200,
        },
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


def test_search_people_serializes_company_linkedin_url(httpx_mock: HTTPXMock) -> None:
    # ``company.linkedin_url`` is honoured here (and on company.tam_by_people), but not on
    # search.companies — hence the PeopleCompanyFilter split.
    httpx_mock.add_response(url=url("/v2/search/people"), method="POST", json=data.PEOPLE_SEARCH)
    _client().search.people(
        company={"linkedin_url": ["https://www.linkedin.com/company/openai"]},
        people={"job_level": [JobLevel.VP]},
    )
    assert _sent_body(httpx_mock) == {
        "company": {"linkedin_url": ["https://www.linkedin.com/company/openai"]},
        "people": {"job_level": ["VP"]},
    }


async def test_async_search_people_serializes_company_linkedin_url(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=url("/v2/search/people"), method="POST", json=data.PEOPLE_SEARCH)
    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        result = await client.search.people(
            company={"linkedin_url": ["https://www.linkedin.com/company/openai"]},
        )
    assert isinstance(result, AsyncCursorPage)
    assert _sent_body(httpx_mock) == {
        "company": {"linkedin_url": ["https://www.linkedin.com/company/openai"]},
    }


def test_search_people_serializes_recent_hire_and_job_scope_flags_inside_people(
    httpx_mock: HTTPXMock,
) -> None:
    # The three flags are keys of ``people`` -- NOT top-level arguments (the API rejects
    # unknown fields at any depth with a 422). ``False`` is a real value, so it is sent.
    httpx_mock.add_response(url=url("/v2/search/people"), method="POST", json=data.PEOPLE_SEARCH)
    _client().search.people(
        people={
            "job_level": [JobLevel.VP],
            "is_recent_hire": True,
            "include_active_jobs": False,
            "include_past_jobs": True,
        },
    )
    body = _sent_body(httpx_mock)
    assert body == {
        "people": {
            "job_level": ["VP"],
            "is_recent_hire": True,
            "include_active_jobs": False,
            "include_past_jobs": True,
        },
    }
    assert not {"is_recent_hire", "include_active_jobs", "include_past_jobs"} & body.keys()


async def test_async_search_people_serializes_recent_hire_and_job_scope_flags(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(url=url("/v2/search/people"), method="POST", json=data.PEOPLE_SEARCH)
    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        await client.search.people(people={"is_recent_hire": True, "include_past_jobs": True})
    assert _sent_body(httpx_mock) == {"people": {"is_recent_hire": True, "include_past_jobs": True}}


def test_search_people_accepts_every_declared_people_filter_variable(
    httpx_mock: HTTPXMock,
) -> None:
    # Static regression, same shape as the ``education`` one: ``search.people`` takes
    # ``SearchPeopleFilter | PeopleFilter``. A bare ``SearchPeopleFilter`` parameter would reject
    # a ``PeopleFilter`` *variable* (``TypedDict`` assignability is structural and the extra
    # optional keys could hold anything), breaking the documented type for this method.
    # mypy/pyright fail the suite on the three calls below if that happens.
    persona: PeopleFilter = {"job_level": [JobLevel.VP], "is_recent_hire": True}
    tam_persona: TamPeopleFilter = {"job_level": [JobLevel.VP], "min_per_company": 2}
    scoped: SearchPeopleFilter = {"job_level": [JobLevel.VP], "include_past_jobs": True}
    httpx_mock.add_response(url=url("/v2/search/people"), method="POST", json=data.PEOPLE_SEARCH)
    httpx_mock.add_response(url=url("/v2/search/people"), method="POST", json=data.PEOPLE_SEARCH)
    httpx_mock.add_response(url=url("/v2/search/people"), method="POST", json=data.PEOPLE_SEARCH)

    client = _client()
    client.search.people(people=persona)
    client.search.people(people=tam_persona)
    client.search.people(people=scoped)

    assert [json.loads(r.content)["people"] for r in httpx_mock.get_requests()] == [
        {"job_level": ["VP"], "is_recent_hire": True},
        {"job_level": ["VP"], "min_per_company": 2},
        {"job_level": ["VP"], "include_past_jobs": True},
    ]


def test_search_people_serializes_mx_and_education_year_filters(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=url("/v2/search/people"), method="POST", json=data.PEOPLE_SEARCH)
    _client().search.people(
        company={
            # Companies with MX data that do not use Google: ``any`` stands for every provider.
            "mx": {"provider": {"include": [MxProvider.ANY], "exclude": [MxProvider.GOOGLE]}},
        },
        people={
            "education": {
                "include": ["Stanford"],
                "start_year": {"min": 2016, "max": 2020},
                "end_year": {"min": 2018},
            },
        },
    )
    assert _sent_body(httpx_mock) == {
        "company": {"mx": {"provider": {"include": ["any"], "exclude": ["google"]}}},
        "people": {
            "education": {
                "include": ["Stanford"],
                "start_year": {"min": 2016, "max": 2020},
                "end_year": {"min": 2018},
            },
        },
    }


def test_search_companies(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/search/companies"), method="POST", json=data.COMPANY_SEARCH
    )
    result = _client().search.companies(company={"employee_range": ["1-10"]}, max_results=1)
    assert isinstance(result, CursorPage)
    assert _sent_body(httpx_mock) == {"company": {"employee_range": ["1-10"]}, "max_results": 1}


def test_search_companies_serializes_mx_filter(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/search/companies"), method="POST", json=data.COMPANY_SEARCH
    )
    _client().search.companies(
        company={"mx": {"provider": {"include": [MxProvider.MICROSOFT, "zoho"]}}}, max_results=1
    )
    assert _sent_body(httpx_mock) == {
        "company": {"mx": {"provider": {"include": ["microsoft", "zoho"]}}},
        "max_results": 1,
    }


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


def test_employee_finder_serializes_is_recent_hire(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/search/employee-finder"), method="POST", json=data.EMPLOYEE_FINDER
    )
    _client().search.employee_finder(
        company_linkedin_url="https://www.linkedin.com/company/openai", is_recent_hire=True
    )
    assert _sent_body(httpx_mock) == {
        "company_linkedin_url": "https://www.linkedin.com/company/openai",
        "is_recent_hire": True,
    }


def test_jobs_search_serializes_job_and_company_filters(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=url("/v2/jobs/search"), method="POST", json=data.JOB_SEARCH)
    result = _client().jobs.search(
        job={
            "title": {"include": ["Growth Marketing"]},
            "seniority": {"include": [Seniority._2_5]},
            "employment_type": {"include": [EmploymentType.FULL_TIME]},
            "work_arrangement": {"exclude": [WorkArrangement.ON_SITE]},
            "location": {"country_code": {"include": ["US"]}},
            "date_posted": {"last_days": 30},
        },
        company={
            "is_agency": False,
            "industry": {"include": [Industry.SOFTWARE_DEVELOPMENT]},
            "size": {"include": ["1001-5000"]},
            "hq": {"city": {"include": ["San Francisco"]}},
        },
        max_results=1,
    )

    assert isinstance(result, CursorPage)
    assert result.results[0].title == "Growth Marketing Manager, SMB Ads"
    body = _sent_body(httpx_mock)
    assert body == {
        "job": {
            "title": {"include": ["Growth Marketing"]},
            "seniority": {"include": ["2-5"]},
            "employment_type": {"include": ["FULL_TIME"]},
            "work_arrangement": {"exclude": ["On-site"]},
            "location": {"country_code": {"include": ["US"]}},
            "date_posted": {"last_days": 30},
        },
        "company": {
            "is_agency": False,
            "industry": {"include": ["Software Development"]},
            "size": {"include": ["1001-5000"]},
            "hq": {"city": {"include": ["San Francisco"]}},
        },
        "max_results": 1,
    }
    assert "cursor" not in body  # None args are omitted


def test_jobs_search_passes_bracketed_exact_match_phrases_through_verbatim(
    httpx_mock: HTTPXMock,
) -> None:
    # ``[brackets]`` are the API's exact-match syntax on job.title and company.hq.city/state
    # (2026-10-15). They are just part of the string: the client must not strip or escape them.
    httpx_mock.add_response(url=url("/v2/jobs/search"), method="POST", json=data.JOB_SEARCH)
    _client().jobs.search(
        job={"title": {"include": ["[Head of Sales]"], "exclude": ["[Intern]"]}},
        company={"hq": {"city": {"include": ["[San Francisco]"]}, "state": {"exclude": ["[CA]"]}}},
    )
    assert _sent_body(httpx_mock) == {
        "job": {"title": {"include": ["[Head of Sales]"], "exclude": ["[Intern]"]}},
        "company": {
            "hq": {"city": {"include": ["[San Francisco]"]}, "state": {"exclude": ["[CA]"]}}
        },
    }


def test_jobs_company_scopes_to_company_url(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=url("/v2/jobs/company"), method="POST", json=data.COMPANY_JOBS)
    result = _client().jobs.company(
        company_linkedin_url="https://www.linkedin.com/company/openai",
        job={"field": {"include": ["Software Engineering"]}},
        max_results=1,
    )
    assert isinstance(result, CursorPage)
    assert result.results[0].company_name == "OpenAI"
    assert _sent_body(httpx_mock) == {
        "company_linkedin_url": "https://www.linkedin.com/company/openai",
        "job": {"field": {"include": ["Software Engineering"]}},
        "max_results": 1,
    }


async def test_async_jobs_search(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=url("/v2/jobs/search"), method="POST", json=data.JOB_SEARCH)
    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        result = await client.jobs.search(job={"title": {"include": ["Engineer"]}})
    assert isinstance(result, AsyncCursorPage)
    assert result.results[0].title == "Growth Marketing Manager, SMB Ads"


def test_company_tam_by_jobs_serializes_min_per_company(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/company/tam-by-jobs"), method="POST", json=data.TAM_BY_JOBS
    )
    result = _client().company.tam_by_jobs(
        job={"title": {"include": ["Account Executive"]}, "min_per_company": 3},
        company={"industry": {"include": [Industry.SOFTWARE_DEVELOPMENT]}},
        max_results=10,
    )

    assert isinstance(result, CursorPage)
    assert result.results[0].matched_jobs == 7
    assert result.results[0].company is not None
    assert result.results[0].company.name == "Google"
    body = _sent_body(httpx_mock)
    assert body == {
        "job": {"title": {"include": ["Account Executive"]}, "min_per_company": 3},
        "company": {"industry": {"include": ["Software Development"]}},
        "max_results": 10,
    }
    assert "cursor" not in body  # None args are omitted


async def test_async_company_tam_by_jobs(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/company/tam-by-jobs"), method="POST", json=data.TAM_BY_JOBS
    )
    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        result = await client.company.tam_by_jobs(
            job={"title": {"include": ["Account Executive"]}, "min_per_company": 3}
        )
    assert isinstance(result, AsyncCursorPage)
    assert result.results[0].matched_jobs == 7


def test_company_tam_by_people_serializes_min_per_company(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/company/tam-by-people"), method="POST", json=data.TAM_BY_PEOPLE
    )
    result = _client().company.tam_by_people(
        company={"industry": {"include": [Industry.SOFTWARE_DEVELOPMENT]}},
        people={
            "job_level": [JobLevel.VP],
            "job_function": [JobFunction.SALES_BUSINESS_DEVELOPMENT],
            "linkedin_url": ["https://www.linkedin.com/in/example"],
            "min_per_company": 5,
        },
        max_results=10,
    )

    assert isinstance(result, CursorPage)
    assert result.results[0].matched_people == 27
    assert result.results[0].company is not None
    assert result.results[0].company.name == "Google"
    body = _sent_body(httpx_mock)
    assert body == {
        "company": {"industry": {"include": ["Software Development"]}},
        "people": {
            "job_level": ["VP"],
            "job_function": ["Sales & Business Development"],
            "linkedin_url": ["https://www.linkedin.com/in/example"],
            "min_per_company": 5,
        },
        "max_results": 10,
    }
    assert "cursor" not in body  # None args are omitted


def test_company_tam_by_people_serializes_recent_hire_and_new_filters(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(
        url=url("/v2/company/tam-by-people"), method="POST", json=data.TAM_BY_PEOPLE
    )
    _client().company.tam_by_people(
        company={"mx": {"provider": {"exclude": [MxProvider.ANY]}}},
        people={
            "education": {"end_year": {"min": 2022, "max": 2025}},
            "min_per_company": 3,
            "is_recent_hire": True,
        },
    )
    body = _sent_body(httpx_mock)
    assert body == {
        "company": {"mx": {"provider": {"exclude": ["any"]}}},
        "people": {
            "education": {"end_year": {"min": 2022, "max": 2025}},
            "min_per_company": 3,
            "is_recent_hire": True,
        },
    }
    assert "is_recent_hire" not in body  # a key of ``people``, not a top-level argument


async def test_async_company_tam_by_people(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/company/tam-by-people"), method="POST", json=data.TAM_BY_PEOPLE
    )
    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        result = await client.company.tam_by_people(people={"min_per_company": 5})
    assert isinstance(result, AsyncCursorPage)
    assert result.results[0].matched_people == 27
    assert _sent_body(httpx_mock) == {"people": {"min_per_company": 5}}


async def test_async_company_tam_by_people_serializes_is_recent_hire(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(
        url=url("/v2/company/tam-by-people"), method="POST", json=data.TAM_BY_PEOPLE
    )
    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        await client.company.tam_by_people(people={"is_recent_hire": True})
    assert _sent_body(httpx_mock) == {"people": {"is_recent_hire": True}}


def test_changelog_list_public_get_with_query_params(httpx_mock: HTTPXMock) -> None:
    # Matched by method only: the request URL carries a query string, asserted below.
    httpx_mock.add_response(method="GET", json=data.CHANGELOG)
    # Deliberately-invalid key: the endpoint is public, so this still succeeds.
    client = BlitzAPI(api_key="not-a-real-key", rate_limit_rps=None)
    entries = client.changelog.list(days=7, limit=25)

    assert isinstance(entries, list)
    assert isinstance(entries[0], ChangelogEntry)
    assert entries[0].type == "feature"
    assert entries[0].affected_endpoints == ["/v2/company/tam-by-jobs"]
    request = httpx_mock.get_request()
    assert request is not None
    assert request.method == "GET"
    assert request.url.params.get("days") == "7"
    assert request.url.params.get("limit") == "25"


def test_changelog_list_omits_absent_query_params(httpx_mock: HTTPXMock) -> None:
    # No args: the URL is the bare trailing-slash path with no query string.
    httpx_mock.add_response(url=url("/changelog/"), method="GET", json=data.CHANGELOG)
    _client().changelog.list()
    request = httpx_mock.get_request()
    assert request is not None
    assert request.url.query == b""


def test_changelog_list_drops_only_the_unset_query_param(httpx_mock: HTTPXMock) -> None:
    # The mixed case, which the both-unset test above cannot catch: the client strips
    # ``None`` params, so an unset one is absent rather than sent as an empty ``limit=``.
    httpx_mock.add_response(method="GET", json=data.CHANGELOG)
    _client().changelog.list(days=7)
    request = httpx_mock.get_request()
    assert request is not None
    assert request.url.query == b"days=7"


async def test_async_changelog_list(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(method="GET", json=data.CHANGELOG)
    async with AsyncBlitzAPI(api_key="not-a-real-key", rate_limit_rps=None) as client:
        entries = await client.changelog.list(limit=25)
    assert [e.type for e in entries] == ["feature", "fix"]
    request = httpx_mock.get_request()
    assert request is not None
    assert request.method == "GET"
    assert request.url.params.get("limit") == "25"


def test_waterfall_icp(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/search/waterfall-icp-keyword"), method="POST", json=data.WATERFALL_ICP
    )
    result = _client().search.waterfall_icp(
        company_linkedin_url="https://www.linkedin.com/company/openai",
        cascade=[{"include_title": ["CEO"]}],  # location / include_headline_search optional
        profile_min_connections=100,
        max_results=5,
    )
    assert isinstance(result, WaterfallIcpResponse)
    body = _sent_body(httpx_mock)
    assert body["cascade"][0]["include_title"] == ["CEO"]
    assert body["profile_min_connections"] == 100
    # The three new top-level flags are absent unless set.
    assert not {"is_recent_hire", "include_active_jobs", "include_past_jobs"} & body.keys()


def test_waterfall_icp_serializes_job_scope_flags_per_cascade_tier(httpx_mock: HTTPXMock) -> None:
    # The flags live on each tier, so one cascade can try recent hires first and fall back to
    # everyone. They are not arguments of ``waterfall_icp`` itself.
    httpx_mock.add_response(
        url=url("/v2/search/waterfall-icp-keyword"), method="POST", json=data.WATERFALL_ICP
    )
    _client().search.waterfall_icp(
        company_linkedin_url="https://www.linkedin.com/company/openai",
        cascade=[
            {
                "include_title": ["CEO"],
                "is_recent_hire": True,
                "include_active_jobs": False,
                "include_past_jobs": True,
            },
            {"include_title": ["CTO"]},
        ],
    )
    body = _sent_body(httpx_mock)
    assert body == {
        "company_linkedin_url": "https://www.linkedin.com/company/openai",
        "cascade": [
            {
                "include_title": ["CEO"],
                "is_recent_hire": True,
                "include_active_jobs": False,
                "include_past_jobs": True,
            },
            {"include_title": ["CTO"]},
        ],
    }
    assert not {"is_recent_hire", "include_active_jobs", "include_past_jobs"} & body.keys()


def test_current_date(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/utils/current-date"), method="POST", json=data.CURRENT_DATE
    )
    result = _client().utils.current_date(region="America/New_York")
    assert isinstance(result, CurrentDateResponse)
    assert _sent_body(httpx_mock) == {"region": "America/New_York"}


def test_current_date_no_region(httpx_mock: HTTPXMock) -> None:
    # region is optional; omitting it sends an empty body so the server default applies.
    httpx_mock.add_response(
        url=url("/v2/utils/current-date"), method="POST", json=data.CURRENT_DATE
    )
    _client().utils.current_date()
    assert _sent_body(httpx_mock) == {}


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
    assert result.found is True
    assert _sent_body(httpx_mock) == {
        "company_linkedin_url": "https://www.linkedin.com/company/openai"
    }


def test_company_distribution_by_country_serializes_is_recent_hire(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=url("/v2/enrichment/company-distribution-by-country"),
        method="POST",
        json=data.COUNTRY_DISTRIBUTION,
    )
    _client().enrichment.company_distribution_by_country(
        company_linkedin_url="https://www.linkedin.com/company/openai", is_recent_hire=True
    )
    assert _sent_body(httpx_mock) == {
        "company_linkedin_url": "https://www.linkedin.com/company/openai",
        "is_recent_hire": True,
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
    assert result.found is True
    assert _sent_body(httpx_mock) == {
        "company_linkedin_url": "https://www.linkedin.com/company/openai"
    }


async def test_async_company_distribution_by_department_serializes_is_recent_hire(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(
        url=url("/v2/enrichment/company-distribution-by-department"),
        method="POST",
        json=data.DEPARTMENT_DISTRIBUTION,
    )
    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        await client.enrichment.company_distribution_by_department(
            company_linkedin_url="https://www.linkedin.com/company/openai", is_recent_hire=True
        )
    assert _sent_body(httpx_mock) == {
        "company_linkedin_url": "https://www.linkedin.com/company/openai",
        "is_recent_hire": True,
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
