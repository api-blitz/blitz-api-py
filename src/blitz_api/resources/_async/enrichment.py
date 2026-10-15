"""The Enrichment resource: ``client.enrichment``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._compat import TimeoutParam
from ...types.enrichment import (
    CompanyDistributionByCountryResponse,
    CompanyDistributionByDepartmentResponse,
    CompanyEnrichmentResponse,
    DomainToLinkedinResponse,
    EmailEnrichmentResponse,
    EmailToPersonResponse,
    LinkedinToDomainResponse,
    PersonEnrichmentResponse,
    PhoneEnrichmentResponse,
    PhoneToPersonResponse,
)

if TYPE_CHECKING:
    from ..._client import AsyncBlitzAPI

_PERSON = "/v2/enrichment/person"
_EMAIL = "/v2/enrichment/email"
_PHONE = "/v2/enrichment/phone"
_EMAIL_TO_PERSON = "/v2/enrichment/email-to-person"
_PHONE_TO_PERSON = "/v2/enrichment/phone-to-person"
_COMPANY = "/v2/enrichment/company"
_DOMAIN_TO_LINKEDIN = "/v2/enrichment/domain-to-linkedin"
_LINKEDIN_TO_DOMAIN = "/v2/enrichment/linkedin-to-domain"
_DISTRIBUTION_BY_COUNTRY = "/v2/enrichment/company-distribution-by-country"
_DISTRIBUTION_BY_DEPARTMENT = "/v2/enrichment/company-distribution-by-department"


class AsyncEnrichmentResource:
    def __init__(self, client: AsyncBlitzAPI) -> None:
        self._client = client

    async def person(
        self, *, person_linkedin_url: str, timeout: TimeoutParam = None
    ) -> PersonEnrichmentResponse:
        """Enrich a person from their LinkedIn profile URL.

        Returns their whole career in ``person.experiences`` (every position held, in
        profile order), plus education, skills and certifications. The API bills
        **1 record on success**.
        """
        return await self._client._request(
            "POST",
            _PERSON,
            body={"person_linkedin_url": person_linkedin_url},
            cast_to=PersonEnrichmentResponse,
            timeout=timeout,
        )

    async def email(
        self, *, person_linkedin_url: str, timeout: TimeoutParam = None
    ) -> EmailEnrichmentResponse:
        """Find a verified work email from a LinkedIn profile URL."""
        return await self._client._request(
            "POST",
            _EMAIL,
            body={"person_linkedin_url": person_linkedin_url},
            cast_to=EmailEnrichmentResponse,
            timeout=timeout,
        )

    async def phone(
        self, *, person_linkedin_url: str, timeout: TimeoutParam = None
    ) -> PhoneEnrichmentResponse:
        """Find a phone number from a LinkedIn profile URL (US only)."""
        return await self._client._request(
            "POST",
            _PHONE,
            body={"person_linkedin_url": person_linkedin_url},
            cast_to=PhoneEnrichmentResponse,
            timeout=timeout,
        )

    async def email_to_person(
        self, *, email: str, timeout: TimeoutParam = None
    ) -> EmailToPersonResponse:
        """Resolve a work email to a full person profile."""
        return await self._client._request(
            "POST",
            _EMAIL_TO_PERSON,
            body={"email": email},
            cast_to=EmailToPersonResponse,
            timeout=timeout,
        )

    async def phone_to_person(
        self, *, phone: str, timeout: TimeoutParam = None
    ) -> PhoneToPersonResponse:
        """Resolve a phone number to a full person profile."""
        return await self._client._request(
            "POST",
            _PHONE_TO_PERSON,
            body={"phone": phone},
            cast_to=PhoneToPersonResponse,
            timeout=timeout,
        )

    async def company(
        self, *, company_linkedin_url: str, timeout: TimeoutParam = None
    ) -> CompanyEnrichmentResponse:
        """Resolve a company LinkedIn URL to a full company profile."""
        return await self._client._request(
            "POST",
            _COMPANY,
            body={"company_linkedin_url": company_linkedin_url},
            cast_to=CompanyEnrichmentResponse,
            timeout=timeout,
        )

    async def domain_to_linkedin(
        self, *, domain: str, timeout: TimeoutParam = None
    ) -> DomainToLinkedinResponse:
        """Resolve a website domain to a company LinkedIn URL."""
        return await self._client._request(
            "POST",
            _DOMAIN_TO_LINKEDIN,
            body={"domain": domain},
            cast_to=DomainToLinkedinResponse,
            timeout=timeout,
        )

    async def linkedin_to_domain(
        self, *, company_linkedin_url: str, timeout: TimeoutParam = None
    ) -> LinkedinToDomainResponse:
        """Resolve a company LinkedIn URL to its email domain."""
        return await self._client._request(
            "POST",
            _LINKEDIN_TO_DOMAIN,
            body={"company_linkedin_url": company_linkedin_url},
            cast_to=LinkedinToDomainResponse,
            timeout=timeout,
        )

    async def company_distribution_by_country(
        self,
        *,
        company_linkedin_url: str,
        is_recent_hire: bool | None = None,
        timeout: TimeoutParam = None,
    ) -> CompanyDistributionByCountryResponse:
        """Get a company's employee count broken down by country.

        Counts **people**, not jobs: since 2026-10-14 a person with a second job at the
        company is no longer counted twice in ``count`` / ``total_employees``.

        Countries are reported as ISO 3166-1 alpha-2 codes (e.g. ``US``, ``GB``);
        employees whose country can't be determined are bucketed under ``"unknown"``.

        ``is_recent_hire=True`` counts only people whose current job at the company started
        in the last 90 days (a job with no start date is not counted).
        """
        return await self._client._request(
            "POST",
            _DISTRIBUTION_BY_COUNTRY,
            body={"company_linkedin_url": company_linkedin_url, "is_recent_hire": is_recent_hire},
            cast_to=CompanyDistributionByCountryResponse,
            timeout=timeout,
        )

    async def company_distribution_by_department(
        self,
        *,
        company_linkedin_url: str,
        is_recent_hire: bool | None = None,
        timeout: TimeoutParam = None,
    ) -> CompanyDistributionByDepartmentResponse:
        """Get a company's employee count broken down by department.

        Employees with no classified department are counted under ``"Other"``.

        ``is_recent_hire=True`` counts only people whose current job at the company started
        in the last 90 days (a job with no start date is not counted).
        """
        return await self._client._request(
            "POST",
            _DISTRIBUTION_BY_DEPARTMENT,
            body={"company_linkedin_url": company_linkedin_url, "is_recent_hire": is_recent_hire},
            cast_to=CompanyDistributionByDepartmentResponse,
            timeout=timeout,
        )
