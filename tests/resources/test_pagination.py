"""Auto-pagination tests for the search resource (sync + async)."""

from __future__ import annotations

import json
from typing import Any

import pytest
from pytest_httpx import HTTPXMock

from blitz_api import AsyncBlitzAPI, BlitzAPI, BlitzError, CursorPage
from blitz_api.types import Person
from tests import data
from tests.conftest import TEST_KEY, url

_PEOPLE = url("/v2/search/people")
_EMPLOYEE_FINDER = url("/v2/search/employee-finder")
_JOBS_SEARCH = url("/v2/jobs/search")
_JOBS_COMPANY = url("/v2/jobs/company")
_TAM_BY_JOBS = url("/v2/company/tam-by-jobs")


def _client() -> BlitzAPI:
    return BlitzAPI(api_key=TEST_KEY, rate_limit_rps=None)


# --- cursor-based (people) ---------------------------------------------------------


def test_cursor_auto_paginates_items(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE1)
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE2)

    names = [p.full_name for p in _client().search.people(max_results=1)]

    assert names == ["Person One", "Person Two"]
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    # The second request carries the cursor returned by the first page.
    assert json.loads(requests[1].content)["cursor"] == "next-cursor"


def test_cursor_stops_when_cursor_is_null(httpx_mock: HTTPXMock) -> None:
    # Only the first (cursor=null) page is served; iteration must not request more.
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE2)
    names = [p.full_name for p in _client().search.people()]
    assert names == ["Person Two"]
    assert len(httpx_mock.get_requests()) == 1


def test_max_items_caps_iteration(httpx_mock: HTTPXMock) -> None:
    # max_items=1 stops after the first item, so page 2 is never fetched.
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE1)
    page = _client().search.people(max_results=1)
    names = [p.full_name for p in page.auto_paging_iter(max_items=1)]
    assert names == ["Person One"]
    assert len(httpx_mock.get_requests()) == 1


def test_iter_pages_yields_page_objects(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE1)
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE2)
    pages = list(_client().search.people(max_results=1).iter_pages())
    assert len(pages) == 2
    assert pages[0].cursor == "next-cursor"
    assert pages[1].cursor is None
    assert all(isinstance(p, CursorPage) for p in pages)


def test_max_pages_caps_iteration(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE1)
    pages = list(_client().search.people(max_results=1).iter_pages(max_pages=1))
    assert len(pages) == 1
    assert len(httpx_mock.get_requests()) == 1


def test_get_next_page(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE1)
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE2)
    first = _client().search.people(max_results=1)
    second = first.get_next_page()
    assert second is not None
    assert second.results[0].full_name == "Person Two"
    assert second.get_next_page() is None  # cursor=null -> no further request
    assert len(httpx_mock.get_requests()) == 2


def test_per_call_timeout_propagates_across_pages(httpx_mock: HTTPXMock) -> None:
    # A per-call timeout must apply to EVERY auto-paged request, not just the first page.
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE1)
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE2)

    list(_client().search.people(max_results=1, timeout=7.5))

    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    # The second (auto-paged) request carries the same override as the first.
    assert requests[0].extensions["timeout"]["read"] == 7.5
    assert requests[1].extensions["timeout"]["read"] == 7.5


def test_cursor_continues_past_empty_intermediate_page(httpx_mock: HTTPXMock) -> None:
    # A sparse page (empty results but a valid forward cursor) must keep paging, not stop.
    sparse: dict[str, Any] = {**data.PEOPLE_SEARCH_PAGE1, "results": [], "cursor": "next-cursor"}
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=sparse)
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE2)

    names = [p.full_name for p in _client().search.people(max_results=1)]

    assert names == ["Person Two"]  # nothing lost to the empty intermediate page
    assert len(httpx_mock.get_requests()) == 2


def test_cursor_guard_aborts_on_non_advancing_cursor(httpx_mock: HTTPXMock) -> None:
    # The API hands back the same cursor it was given; iteration must abort with a clear error
    # instead of looping forever (re-fetching and re-billing the same page).
    stuck = {**data.PEOPLE_SEARCH_PAGE1, "cursor": "stuck"}
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=stuck)
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=stuck)

    with pytest.raises(BlitzError, match="Cursor did not advance"):
        list(_client().search.people(max_results=1))

    # First fetch (no cursor) + second (cursor=stuck); the third loop was aborted pre-request.
    assert len(httpx_mock.get_requests()) == 2


def test_cursor_guard_allows_distinct_cursors(httpx_mock: HTTPXMock) -> None:
    # Distinct cursors on consecutive pages must NOT trip the guard — it fires only on a repeat.
    mid = {**data.PEOPLE_SEARCH_PAGE1, "cursor": "second-cursor"}
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE1)
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=mid)
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE2)

    names = [p.full_name for p in _client().search.people(max_results=1)]

    assert names == ["Person One", "Person One", "Person Two"]
    assert len(httpx_mock.get_requests()) == 3


def test_collect_drains_all_items(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE1)
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE2)

    people = _client().search.people(max_results=1).collect()

    assert [p.full_name for p in people] == ["Person One", "Person Two"]
    assert len(httpx_mock.get_requests()) == 2


def test_collect_honors_max_items(httpx_mock: HTTPXMock) -> None:
    # max_items caps the collected list and stops fetching further pages.
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE1)

    people = _client().search.people(max_results=1).collect(max_items=1)

    assert [p.full_name for p in people] == ["Person One"]
    assert len(httpx_mock.get_requests()) == 1


# --- cursor-based (jobs.search / jobs.company) -------------------------------------


def test_jobs_search_auto_paginates_items(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_JOBS_SEARCH, method="POST", json=data.JOB_SEARCH_PAGE1)
    httpx_mock.add_response(url=_JOBS_SEARCH, method="POST", json=data.JOB_SEARCH_PAGE2)

    titles = [j.title for j in _client().jobs.search(max_results=1)]

    assert titles == ["Job One", "Job Two"]
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert json.loads(requests[1].content)["cursor"] == "next-cursor"


def test_jobs_company_re_sends_scope_url_on_every_page(httpx_mock: HTTPXMock) -> None:
    # The scoping URL must be echoed on the follow-up page, not just the first request.
    httpx_mock.add_response(url=_JOBS_COMPANY, method="POST", json=data.JOB_SEARCH_PAGE1)
    httpx_mock.add_response(url=_JOBS_COMPANY, method="POST", json=data.JOB_SEARCH_PAGE2)

    company_url = "https://www.linkedin.com/company/openai"
    titles = [
        j.title for j in _client().jobs.company(company_linkedin_url=company_url, max_results=1)
    ]

    assert titles == ["Job One", "Job Two"]
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    second = json.loads(requests[1].content)
    assert second["company_linkedin_url"] == company_url
    assert second["cursor"] == "next-cursor"


def test_jobs_cursor_guard_aborts_on_non_advancing_cursor(httpx_mock: HTTPXMock) -> None:
    stuck = {**data.JOB_SEARCH_PAGE1, "cursor": "stuck"}
    httpx_mock.add_response(url=_JOBS_SEARCH, method="POST", json=stuck)
    httpx_mock.add_response(url=_JOBS_SEARCH, method="POST", json=stuck)

    with pytest.raises(BlitzError, match="Cursor did not advance"):
        list(_client().jobs.search(max_results=1))

    assert len(httpx_mock.get_requests()) == 2


# --- cursor-based (company.tam_by_jobs) --------------------------------------------


def test_tam_by_jobs_streams_matches_across_pages(httpx_mock: HTTPXMock) -> None:
    # Self-contained (no data.py fixtures): page 1 returns a cursor; page 2 returns
    # cursor=null and terminates the walk.
    httpx_mock.add_response(
        url=_TAM_BY_JOBS,
        method="POST",
        json={
            "results": [{"company": {"name": "TAM One"}, "matched_jobs": 3}],
            "results_length": 1,
            "max_results": 1,
            "cursor": "next-cursor",
        },
    )
    httpx_mock.add_response(
        url=_TAM_BY_JOBS,
        method="POST",
        json={
            "results": [{"company": {"name": "TAM Two"}, "matched_jobs": 5}],
            "results_length": 1,
            "max_results": 1,
            "cursor": None,
        },
    )

    matches = list(_client().company.tam_by_jobs(max_results=1))

    names = [m.company.name if m.company else None for m in matches]
    counts = [m.matched_jobs for m in matches]
    assert names == ["TAM One", "TAM Two"]
    assert counts == [3, 5]
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    # First request omits the cursor; the second carries the cursor page 1 returned.
    assert "cursor" not in json.loads(requests[0].content)
    assert json.loads(requests[1].content)["cursor"] == "next-cursor"


# --- page-number-based (employee_finder) -------------------------------------------


def test_page_number_auto_paginates_items(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_EMPLOYEE_FINDER, method="POST", json=data.EMPLOYEE_FINDER_PAGE1)
    httpx_mock.add_response(url=_EMPLOYEE_FINDER, method="POST", json=data.EMPLOYEE_FINDER_PAGE2)

    names = [
        p.full_name
        for p in _client().search.employee_finder(
            company_linkedin_url="https://www.linkedin.com/company/openai", max_results=1
        )
    ]

    assert names == ["Employee One", "Employee Two"]
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert json.loads(requests[1].content)["page"] == 2


def test_page_number_stops_at_total_pages(httpx_mock: HTTPXMock) -> None:
    # Single page where page == total_pages: iteration must not request more.
    httpx_mock.add_response(url=_EMPLOYEE_FINDER, method="POST", json=data.EMPLOYEE_FINDER_PAGE2)
    names = [
        p.full_name
        for p in _client().search.employee_finder(
            company_linkedin_url="https://www.linkedin.com/company/openai"
        )
    ]
    assert names == ["Employee Two"]
    assert len(httpx_mock.get_requests()) == 1


def test_page_number_advances_when_page_field_absent(httpx_mock: HTTPXMock) -> None:
    # If the server omits `page` but reports total_pages, iteration must still advance by
    # falling back to the requested page (defaulting to 1), not silently stop after page 1.
    page1_no_page = {k: v for k, v in data.EMPLOYEE_FINDER_PAGE1.items() if k != "page"}
    httpx_mock.add_response(url=_EMPLOYEE_FINDER, method="POST", json=page1_no_page)
    httpx_mock.add_response(url=_EMPLOYEE_FINDER, method="POST", json=data.EMPLOYEE_FINDER_PAGE2)

    names = [
        p.full_name
        for p in _client().search.employee_finder(
            company_linkedin_url="https://www.linkedin.com/company/openai"
        )
    ]

    assert names == ["Employee One", "Employee Two"]
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert json.loads(requests[1].content)["page"] == 2


# --- forward compatibility ---------------------------------------------------------


def test_unknown_fields_on_a_page_are_preserved() -> None:
    page = CursorPage[Person].model_validate({**data.PEOPLE_SEARCH_PAGE2, "next_token": "x"})
    assert page.results[0].full_name == "Person Two"
    assert page.model_extra == {"next_token": "x"}


# --- async parity ------------------------------------------------------------------


async def test_async_cursor_auto_paginates(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE1)
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE2)

    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        names = [p.full_name async for p in await client.search.people(max_results=1)]

    assert names == ["Person One", "Person Two"]
    assert len(httpx_mock.get_requests()) == 2


async def test_async_iter_pages_and_max_items(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE1)

    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        page = await client.search.people(max_results=1)
        names = [p.full_name async for p in page.auto_paging_iter(max_items=1)]

    assert names == ["Person One"]
    assert len(httpx_mock.get_requests()) == 1


async def test_async_cursor_guard_aborts(httpx_mock: HTTPXMock) -> None:
    stuck = {**data.PEOPLE_SEARCH_PAGE1, "cursor": "stuck"}
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=stuck)
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=stuck)

    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        page = await client.search.people(max_results=1)
        with pytest.raises(BlitzError, match="Cursor did not advance"):
            async for _ in page:
                pass

    assert len(httpx_mock.get_requests()) == 2


async def test_async_collect_drains_all_items(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE1)
    httpx_mock.add_response(url=_PEOPLE, method="POST", json=data.PEOPLE_SEARCH_PAGE2)

    async with AsyncBlitzAPI(api_key=TEST_KEY, rate_limit_rps=None) as client:
        page = await client.search.people(max_results=1)
        people = await page.collect()

    assert [p.full_name for p in people] == ["Person One", "Person Two"]
    assert len(httpx_mock.get_requests()) == 2
