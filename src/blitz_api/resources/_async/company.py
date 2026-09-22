"""The Company resource: ``client.company``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._compat import TimeoutParam
from ..._pagination_async import AsyncCursorPage
from ...types.company import TamByJobsMatch, TamByPeopleMatch
from ...types.filters import CompanyFilter, JobCompanyFilter, TamJobFilter, TamPeopleFilter

if TYPE_CHECKING:
    from ..._client import AsyncBlitzAPI

_TAM_BY_JOBS = "/v2/company/tam-by-jobs"
_TAM_BY_PEOPLE = "/v2/company/tam-by-people"


class AsyncCompanyResource:
    def __init__(self, client: AsyncBlitzAPI) -> None:
        self._client = client

    async def tam_by_jobs(
        self,
        *,
        job: TamJobFilter | None = None,
        company: JobCompanyFilter | None = None,
        max_results: int | None = None,
        cursor: str | None = None,
        timeout: TimeoutParam = None,
    ) -> AsyncCursorPage[TamByJobsMatch]:
        """Build a Total Addressable Market of companies from live hiring signals.

        Combine job-level filters (title, description, seniority, ...) with company
        firmographics, and get back each matching company plus how many of its current
        postings matched (``matched_jobs``). Use ``job["min_per_company"]`` to require a
        minimum number of matching postings per company.

        Cursor-paginated: auto-paginates over every ``{company, matched_jobs}`` match when
        the result is iterated; use ``.iter_pages()`` or the ``cursor=`` arg for manual
        control. The API bills **1 record per result returned**; bound spend with
        ``max_items`` on ``.collect()`` / ``.auto_paging_iter()``.
        """
        body = {"job": job, "company": company, "max_results": max_results, "cursor": cursor}
        return await self._client._request(
            "POST",
            _TAM_BY_JOBS,
            body=body,
            cast_to=AsyncCursorPage[TamByJobsMatch],
            timeout=timeout,
        )

    async def tam_by_people(
        self,
        *,
        company: CompanyFilter | None = None,
        people: TamPeopleFilter | None = None,
        max_results: int | None = None,
        cursor: str | None = None,
        timeout: TimeoutParam = None,
    ) -> AsyncCursorPage[TamByPeopleMatch]:
        """Build a Total Addressable Market of companies from headcount signals.

        Takes the same filters as ``search.people`` — company firmographics plus a
        persona — but returns the **distinct companies** employing the matching people
        (deduplicated), each with its ``matched_people`` count. Use
        ``people["min_per_company"]`` to require a minimum number of matching employees
        per company.

        Cursor-paginated: auto-paginates over every ``{company, matched_people}`` match
        when the result is iterated; use ``.iter_pages()`` or the ``cursor=`` arg for
        manual control. When ``min_per_company`` filters heavily a page may come back
        partial — keep paging until the cursor is exhausted. The API bills **1 record per
        result returned**; bound spend with ``max_items`` on ``.collect()`` /
        ``.auto_paging_iter()``.
        """
        body = {"company": company, "people": people, "max_results": max_results, "cursor": cursor}
        return await self._client._request(
            "POST",
            _TAM_BY_PEOPLE,
            body=body,
            cast_to=AsyncCursorPage[TamByPeopleMatch],
            timeout=timeout,
        )
