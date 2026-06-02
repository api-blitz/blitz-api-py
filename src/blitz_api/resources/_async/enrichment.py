"""The Enrichment resource: ``client.enrichment``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._compat import TimeoutParam
from ...types.enrichment import (
    CompanyEnrichmentResponse,
    DomainToLinkedinResponse,
    EmailEnrichmentResponse,
    EmailToPersonResponse,
    LinkedinToDomainResponse,
    PhoneEnrichmentResponse,
    PhoneToPersonResponse,
)

if TYPE_CHECKING:
    from ..._client import AsyncBlitzAPI

_EMAIL = "/v2/enrichment/email"
_PHONE = "/v2/enrichment/phone"
_EMAIL_TO_PERSON = "/v2/enrichment/email-to-person"
_PHONE_TO_PERSON = "/v2/enrichment/phone-to-person"
_COMPANY = "/v2/enrichment/company"
_DOMAIN_TO_LINKEDIN = "/v2/enrichment/domain-to-linkedin"
_LINKEDIN_TO_DOMAIN = "/v2/enrichment/linkedin-to-domain"


class AsyncEnrichmentResource:
    def __init__(self, client: AsyncBlitzAPI) -> None:
        self._client = client

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
