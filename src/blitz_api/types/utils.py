"""Response models for the Utilities resource."""

from __future__ import annotations

from ._models import BlitzModel

__all__ = [
    "CurrentDateResponse",
    "EmploymentDistributionItem",
    "CompanyEmploymentDistributionResponse",
    "DepartmentDistributionItem",
    "CompanyDepartmentDistributionResponse",
]


class CurrentDateResponse(BlitzModel):
    """Result of ``utils.current_date``."""

    datetime: str | None = None
    timestamp: int | None = None
    timezone: str | None = None
    timezone_name: str | None = None


class EmploymentDistributionItem(BlitzModel):
    """Employee count for a single country."""

    country: str | None = None
    count: int | None = None


class CompanyEmploymentDistributionResponse(BlitzModel):
    """Result of ``utils.company_employment_distribution``."""

    company_linkedin_url: str | None = None
    total_employees: int | None = None
    distribution: list[EmploymentDistributionItem] = []


class DepartmentDistributionItem(BlitzModel):
    """Employee count for a single department (Blitz job function).

    Employees with no classified department are counted under ``"Other"``.
    """

    department: str | None = None
    count: int | None = None


class CompanyDepartmentDistributionResponse(BlitzModel):
    """Result of ``utils.company_department_distribution``."""

    company_linkedin_url: str | None = None
    total_employees: int | None = None
    distribution: list[DepartmentDistributionItem] = []
