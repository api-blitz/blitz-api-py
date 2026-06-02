"""Auto-pagination tests for the search resource (sync + async)."""

from __future__ import annotations

import json
from typing import Any

from pytest_httpx import HTTPXMock

from blitz_api import AsyncBlitzAPI, BlitzAPI, CursorPage
from blitz_api.types import Person
from tests import data
from tests.conftest import TEST_KEY, url

_PEOPLE = url("/v2/search/people")
_EMPLOYEE_FINDER = url("/v2/search/employee-finder")


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
