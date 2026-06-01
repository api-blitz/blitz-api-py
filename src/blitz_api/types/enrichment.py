"""Response models for the Enrichment resource."""

from __future__ import annotations

from ._models import BlitzModel
from .shared import Company, Person

__all__ = [
    "EmailMatch",
    "EmailEnrichmentResponse",
    "PhoneEnrichmentResponse",
    "EmailToPersonResponse",
    "PhoneToPersonResponse",
    "CompanyEnrichmentResponse",
    "DomainToLinkedinResponse",
    "LinkedinToDomainResponse",
]


class EmailMatch(BlitzModel):
    """A single candidate email returned by ``enrichment.email``."""

    email: str | None = None
    job_order_in_profile: int | None = None
    company_linkedin_url: str | None = None
    email_domain: str | None = None


class EmailEnrichmentResponse(BlitzModel):
    """Result of ``enrichment.email`` (LinkedIn URL -> verified work email)."""

    found: bool | None = None
    email: str | None = None
    all_emails: list[EmailMatch] = []


class PhoneEnrichmentResponse(BlitzModel):
    """Result of ``enrichment.phone`` (LinkedIn URL -> phone)."""

    found: bool | None = None
    phone: str | None = None


class EmailToPersonResponse(BlitzModel):
    """Result of ``enrichment.email_to_person`` (email -> full profile)."""

    found: bool | None = None
    person: Person | None = None


class PhoneToPersonResponse(BlitzModel):
    """Result of ``enrichment.phone_to_person`` (phone -> full profile)."""

    found: bool | None = None
    person: Person | None = None


class CompanyEnrichmentResponse(BlitzModel):
    """Result of ``enrichment.company`` (company LinkedIn URL -> company profile)."""

    found: bool | None = None
    company: Company | None = None


class DomainToLinkedinResponse(BlitzModel):
    """Result of ``enrichment.domain_to_linkedin`` (domain -> company LinkedIn URL)."""

    found: bool | None = None
    company_linkedin_url: str | None = None


class LinkedinToDomainResponse(BlitzModel):
    """Result of ``enrichment.linkedin_to_domain`` (company LinkedIn URL -> email domain)."""

    found: bool | None = None
    email_domain: str | None = None
