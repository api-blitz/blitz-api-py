"""Public type surface for the Blitz API SDK.

Import response models and request filters from here, e.g.::

    from blitz_api.types import Person, CompanyFilter, Industry
"""

from __future__ import annotations

from .account import ActivePlan, KeyInfo
from .enrichment import (
    CompanyCountryDistributionResponse,
    CompanyDepartmentDistributionResponse,
    CompanyEnrichmentResponse,
    CountryDistributionItem,
    DepartmentDistributionItem,
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
    FundingType,
    Industry,
    JobFunction,
    JobLevel,
    SalesRegion,
)
from .filters import (
    CascadeTier,
    CompanyFilter,
    CompanyHQFilter,
    CompanyTypeFilter,
    FundingTypeFilter,
    IndustryFilter,
    KeywordFilter,
    PeopleFilter,
    PeopleJobTitleFilter,
    PeopleLocationFilter,
    RangeFilter,
)
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
    "FundingType",
    "Continent",
    "SalesRegion",
    "JobFunction",
    "JobLevel",
    # filters
    "KeywordFilter",
    "IndustryFilter",
    "CompanyTypeFilter",
    "FundingTypeFilter",
    "RangeFilter",
    "CompanyHQFilter",
    "CompanyFilter",
    "PeopleJobTitleFilter",
    "PeopleLocationFilter",
    "PeopleFilter",
    "CascadeTier",
    # account
    "KeyInfo",
    "ActivePlan",
    # search (paginated results return the page classes exported from `blitz_api`)
    "WaterfallIcpMatch",
    "WaterfallIcpResponse",
    # enrichment
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
    # utils
    "CurrentDateResponse",
]
