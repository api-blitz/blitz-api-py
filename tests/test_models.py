"""Tests that the hand-written response models match the API's example shapes."""

from __future__ import annotations

from blitz_api import CursorPage, PageNumberPage
from blitz_api.types import (
    Company,
    CompanyEmploymentDistributionResponse,
    CompanyEnrichmentResponse,
    CurrentDateResponse,
    DomainToLinkedinResponse,
    EmailEnrichmentResponse,
    EmailToPersonResponse,
    KeyInfo,
    LinkedinToDomainResponse,
    Person,
    PhoneEnrichmentResponse,
    PhoneToPersonResponse,
    WaterfallIcpResponse,
)
from tests import data


def test_key_info_parses() -> None:
    info = KeyInfo.model_validate(data.KEY_INFO)
    assert info.valid is True
    assert info.max_requests_per_seconds == 5
    assert info.allowed_apis == ["/enrichment/email", "/search/people"]
    assert info.active_plans[0].name == "Unlimited Leads"


def test_people_search_parses_nested_person() -> None:
    resp = CursorPage[Person].model_validate(data.PEOPLE_SEARCH)
    assert resp.total_results == 14337505
    person = resp.results[0]
    assert person.full_name == "Beulah Lee"
    assert person.location is not None
    assert person.location.country_code == "US"
    exp = person.experiences[0]
    assert exp.company_name == "Google"
    assert exp.job_location is not None
    assert exp.job_location.city == "Sunnyvale"
    assert person.education[0].degree == "Bachelor's degree"
    assert person.certifications[0].authority == "Google"


def test_company_search_parses() -> None:
    resp = CursorPage[Company].model_validate(data.COMPANY_SEARCH)
    company = resp.results[0]
    assert company.name == "Google"
    assert company.linkedin_id == 1441
    assert company.hq is not None
    assert company.hq.region == "NORAM"
    assert company.specialties == ["search", "cloud"]


def test_employee_finder_is_page_paginated() -> None:
    resp = PageNumberPage[Person].model_validate(data.EMPLOYEE_FINDER)
    assert resp.page == 1
    assert resp.total_pages == 1285
    assert resp.results[0].first_name == "Beulah"


def test_waterfall_icp_wraps_person_with_tier() -> None:
    resp = WaterfallIcpResponse.model_validate(data.WATERFALL_ICP)
    match = resp.results[0]
    assert match.icp == 1
    assert match.ranking == 1
    assert match.person is not None
    assert match.person.full_name == "Beulah Lee"


def test_email_enrichment_parses() -> None:
    resp = EmailEnrichmentResponse.model_validate(data.EMAIL_ENRICHMENT)
    assert resp.found is True
    assert resp.email == "antoine@blitz-agency.com"
    assert resp.all_emails[0].email_domain == "blitz-agency.com"


def test_phone_enrichment_parses() -> None:
    resp = PhoneEnrichmentResponse.model_validate(data.PHONE_ENRICHMENT)
    assert resp.found is True
    assert resp.phone == "+1234567890"


def test_email_to_person_parses() -> None:
    resp = EmailToPersonResponse.model_validate(data.EMAIL_TO_PERSON)
    assert resp.person is not None
    assert resp.person.linkedin_url == "https://www.linkedin.com/in/beulah-lee"


def test_phone_to_person_parses() -> None:
    resp = PhoneToPersonResponse.model_validate(data.PHONE_TO_PERSON)
    assert resp.person is not None


def test_company_enrichment_parses() -> None:
    resp = CompanyEnrichmentResponse.model_validate(data.COMPANY_ENRICHMENT)
    assert resp.company is not None
    assert resp.company.domain == "google.com"


def test_domain_to_linkedin_parses() -> None:
    resp = DomainToLinkedinResponse.model_validate(data.DOMAIN_TO_LINKEDIN)
    assert resp.company_linkedin_url == "https://www.linkedin.com/company/blitz-api"


def test_linkedin_to_domain_parses() -> None:
    resp = LinkedinToDomainResponse.model_validate(data.LINKEDIN_TO_DOMAIN)
    assert resp.email_domain == "blitz-agency.com"


def test_current_date_parses() -> None:
    resp = CurrentDateResponse.model_validate(data.CURRENT_DATE)
    assert resp.timestamp == 1736385600
    assert resp.timezone == "America/New_York"


def test_employment_distribution_parses() -> None:
    resp = CompanyEmploymentDistributionResponse.model_validate(data.EMPLOYMENT_DISTRIBUTION)
    assert resp.total_employees == 1234
    assert resp.distribution[0].country == "US"
    assert resp.distribution[0].count == 900


def test_forward_compatible_unknown_fields_preserved() -> None:
    # A field the SDK doesn't model yet must not break validation.
    payload = {**data.PHONE_ENRICHMENT, "confidence_score": 0.97}
    resp = PhoneEnrichmentResponse.model_validate(payload)
    assert resp.phone == "+1234567890"
    assert resp.model_extra == {"confidence_score": 0.97}


def test_forward_compatible_unknown_nested_fields_preserved() -> None:
    payload = {
        "found": True,
        "person": {"full_name": "X", "new_nested_field": {"a": 1}},
    }
    resp = EmailToPersonResponse.model_validate(payload)
    assert resp.person is not None
    assert resp.person.model_extra == {"new_nested_field": {"a": 1}}
