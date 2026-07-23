"""The Jobs resource: ``client.jobs``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..._compat import TimeoutParam
from ..._pagination_async import AsyncCursorPage
from ...types.filters import JobCompanyFilter, JobFilter
from ...types.jobs import Job

if TYPE_CHECKING:
    from ..._client import AsyncBlitzAPI

_SEARCH = "/v2/jobs/search"
_COMPANY = "/v2/jobs/company"


def _drop_none(**kwargs: Any) -> dict[str, Any]:
    """Build a request body keeping only the arguments the caller provided."""
    return {key: value for key, value in kwargs.items() if value is not None}


class AsyncJobsResource:
    def __init__(self, client: AsyncBlitzAPI) -> None:
        self._client = client

    async def search(
        self,
        *,
        job: JobFilter | None = None,
        company: JobCompanyFilter | None = None,
        max_results: int | None = None,
        cursor: str | None = None,
        timeout: TimeoutParam = None,
    ) -> AsyncCursorPage[Job]:
        """Search live job postings across companies, combining job-level filters
        with company firmographics.

        Auto-paginates over every matching job when the result is iterated; use
        ``.iter_pages()`` or the ``cursor=`` arg for manual control.
        """
        body = _drop_none(job=job, company=company, max_results=max_results, cursor=cursor)
        return await self._client._request(
            "POST", _SEARCH, body=body, cast_to=AsyncCursorPage[Job], timeout=timeout
        )

    async def company(
        self,
        *,
        company_linkedin_url: str,
        job: JobFilter | None = None,
        max_results: int | None = None,
        cursor: str | None = None,
        timeout: TimeoutParam = None,
    ) -> AsyncCursorPage[Job]:
        """List job postings at a single company, scoped by its LinkedIn company URL.

        Auto-paginates over every matching job; use ``.iter_pages()`` or ``cursor=``
        for manual control.
        """
        body = _drop_none(
            company_linkedin_url=company_linkedin_url,
            job=job,
            max_results=max_results,
            cursor=cursor,
        )
        return await self._client._request(
            "POST", _COMPANY, body=body, cast_to=AsyncCursorPage[Job], timeout=timeout
        )
