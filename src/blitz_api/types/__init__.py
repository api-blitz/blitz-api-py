"""Public type surface for the Blitz API SDK.

Import response models and request filters from here, e.g.::

    from blitz_api.types import Person, CompanyFilter, Industry
"""

from __future__ import annotations

from .account import ActivePlan, KeyInfo
from .enrichment import (
    CompanyEnrichmentResponse,
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
    IndustryFilter,
    KeywordFilter,
    PeopleFilter,
    PeopleJobTitleFilter,
    PeopleLocationFilter,
    RangeFilter,
)
from .search import (
    CompanySearchResponse,
    EmployeeFinderResponse,
    PeopleSearchResponse,
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
    CompanyEmploymentDistributionResponse,
    CurrentDateResponse,
    EmploymentDistributionItem,
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
    "Continent",
    "SalesRegion",
    "JobFunction",
    "JobLevel",
    # filters
    "KeywordFilter",
    "IndustryFilter",
    "CompanyTypeFilter",
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
    # search
    "PeopleSearchResponse",
    "CompanySearchResponse",
    "EmployeeFinderResponse",
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
    # utils
    "CurrentDateResponse",
    "EmploymentDistributionItem",
    "CompanyEmploymentDistributionResponse",
]
