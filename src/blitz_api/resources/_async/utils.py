"""The Utilities resource: ``client.utils``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._compat import TimeoutParam
from ...types.utils import CompanyEmploymentDistributionResponse, CurrentDateResponse

if TYPE_CHECKING:
    from ..._client import AsyncBlitzAPI

_CURRENT_DATE = "/v2/utils/current-date"
_EMPLOYMENT_DISTRIBUTION = "/v2/utils/company-employment-distribution"


class AsyncUtilsResource:
    def __init__(self, client: AsyncBlitzAPI) -> None:
        self._client = client

    async def current_date(
        self, *, region: str, timeout: TimeoutParam = None
    ) -> CurrentDateResponse:
        """Get the current server date/time for an IANA timezone (e.g. ``America/New_York``)."""
        return await self._client._request(
            "POST",
            _CURRENT_DATE,
            body={"region": region},
            cast_to=CurrentDateResponse,
            timeout=timeout,
        )

    async def company_employment_distribution(
        self, *, company_linkedin_url: str, timeout: TimeoutParam = None
    ) -> CompanyEmploymentDistributionResponse:
        """Get a company's employee count broken down by country."""
        return await self._client._request(
            "POST",
            _EMPLOYMENT_DISTRIBUTION,
            body={"company_linkedin_url": company_linkedin_url},
            cast_to=CompanyEmploymentDistributionResponse,
            timeout=timeout,
        )
