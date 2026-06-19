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
    "CountryDistributionItem",
    "CompanyCountryDistributionResponse",
    "DepartmentDistributionItem",
    "CompanyDepartmentDistributionResponse",
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


class CountryDistributionItem(BlitzModel):
    """Employee count for a single country.

    ``country`` is an ISO 3166-1 alpha-2 code (e.g. ``"US"``, ``"GB"``), or the
    literal ``"unknown"`` bucket for employees whose country couldn't be determined.
    ``percentage_ratio`` is the bucket's share of ``total_employees`` (0-100, to 2
    decimals).
    """

    country: str | None = None
    count: int | None = None
    percentage_ratio: float | None = None


class CompanyCountryDistributionResponse(BlitzModel):
    """Result of ``enrichment.company_distribution_by_country``.

    Served by ``POST /v2/enrichment/company-distribution-by-country``.
    """

    company_linkedin_url: str | None = None
    total_employees: int | None = None
    distribution: list[CountryDistributionItem] = []


class DepartmentDistributionItem(BlitzModel):
    """Employee count for a single department (Blitz job function).

    Employees with no classified department are counted under ``"Other"``.
    ``percentage_ratio`` is the bucket's share of ``total_employees`` (0-100, to 2
    decimals).
    """

    department: str | None = None
    count: int | None = None
    percentage_ratio: float | None = None


class CompanyDepartmentDistributionResponse(BlitzModel):
    """Result of ``enrichment.company_distribution_by_department``.

    Served by ``POST /v2/enrichment/company-distribution-by-department``.
    """

    company_linkedin_url: str | None = None
    total_employees: int | None = None
    distribution: list[DepartmentDistributionItem] = []
