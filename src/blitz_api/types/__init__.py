"""Public type surface for the Blitz API SDK.

Import response models and request filters from here, e.g.::

    from blitz_api.types import Person, CompanyFilter, Industry
"""

from __future__ import annotations

from .account import ActivePlan, KeyInfo
from .enrichment import (
    CompanyDistributionByCountryItem,
    CompanyDistributionByCountryResponse,
    CompanyDistributionByDepartmentItem,
    CompanyDistributionByDepartmentResponse,
    CompanyEnrichmentResponse,
    DomainToLinkedinMatch,
    DomainToLinkedinResponse,
    EmailEnrichmentResponse,
    EmailMatch,
    EmailToPersonResponse,
    LinkedinToDomainResponse,
    PhoneEnrichmentResponse,
    PhoneToPersonResponse,
)
from .enums import (
    CompanyType,
    Continent,
    EmployeeRange,
    EmploymentType,
    Industry,
    JobFunction,
    JobLevel,
    LastFundingType,
    SalesRegion,
    Seniority,
    WorkArrangement,
)
from .filters import (
    CascadeTier,
    CompanyFilter,
    CompanyHQFilter,
    CompanySizeFilter,
    CompanyTypeFilter,
    DatePostedFilter,
    EmploymentTypeFilter,
    IndustryFilter,
    JobCompanyFilter,
    JobCompanyHQFilter,
    JobFilter,
    JobLocationFilter,
    KeywordFilter,
    LastFundingTypeFilter,
    PeopleFilter,
    PeopleJobTitleFilter,
    PeopleLocationFilter,
    RangeFilter,
    SeniorityFilter,
    WorkArrangementFilter,
)
from .jobs import Job
from .search import (
    WaterfallIcpMatch,
    WaterfallIcpResponse,
)
from .shared import (
    HQ,
    Certification,
    Company,
    Education,
    Experience,
    Location,
    Person,
)
from .utils import (
    CurrentDateResponse,
)

__all__ = [
    # shared
    "Person",
    "Experience",
    "Education",
    "Certification",
    "Location",
    "Company",
    "HQ",
    # enums
    "Industry",
    "CompanyType",
    "EmployeeRange",
    "LastFundingType",
    "Continent",
    "SalesRegion",
    "JobFunction",
    "JobLevel",
    "Seniority",
    "EmploymentType",
    "WorkArrangement",
    # filters
    "KeywordFilter",
    "IndustryFilter",
    "CompanyTypeFilter",
    "LastFundingTypeFilter",
    "RangeFilter",
    "CompanyHQFilter",
    "CompanyFilter",
    "PeopleJobTitleFilter",
    "PeopleLocationFilter",
    "PeopleFilter",
    "CascadeTier",
    "SeniorityFilter",
    "EmploymentTypeFilter",
    "WorkArrangementFilter",
    "JobLocationFilter",
    "DatePostedFilter",
    "JobFilter",
    "CompanySizeFilter",
    "JobCompanyHQFilter",
    "JobCompanyFilter",
    # account
    "KeyInfo",
    "ActivePlan",
    # search (paginated results return the page classes exported from `blitz_api`)
    "WaterfallIcpMatch",
    "WaterfallIcpResponse",
    # jobs (paginated results return the page classes exported from `blitz_api`)
    "Job",
    # enrichment
    "EmailMatch",
    "EmailEnrichmentResponse",
    "PhoneEnrichmentResponse",
    "EmailToPersonResponse",
    "PhoneToPersonResponse",
    "CompanyEnrichmentResponse",
    "DomainToLinkedinMatch",
    "DomainToLinkedinResponse",
    "LinkedinToDomainResponse",
    "CompanyDistributionByCountryItem",
    "CompanyDistributionByCountryResponse",
    "CompanyDistributionByDepartmentItem",
    "CompanyDistributionByDepartmentResponse",
    # utils
    "CurrentDateResponse",
]
