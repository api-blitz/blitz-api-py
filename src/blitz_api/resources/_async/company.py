"""The Company resource: ``client.company``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..._compat import TimeoutParam
from ..._pagination_async import AsyncCursorPage
from ...types.company import TamByJobsMatch
from ...types.filters import JobCompanyFilter, TamJobFilter

if TYPE_CHECKING:
    from ..._client import AsyncBlitzAPI

_TAM_BY_JOBS = "/v2/company/tam-by-jobs"


def _drop_none(**kwargs: Any) -> dict[str, Any]:
    """Build a request body keeping only the arguments the caller provided."""
    return {key: value for key, value in kwargs.items() if value is not None}


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
        control. The API bills **1 credit per result returned**; bound spend with
        ``max_items`` on ``.collect()`` / ``.auto_paging_iter()``.
        """
        body = _drop_none(job=job, company=company, max_results=max_results, cursor=cursor)
        return await self._client._request(
            "POST",
            _TAM_BY_JOBS,
            body=body,
            cast_to=AsyncCursorPage[TamByJobsMatch],
            timeout=timeout,
        )
