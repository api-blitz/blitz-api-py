"""Canonical example response payloads, mirroring the Blitz OpenAPI v2 examples.

Used as deserialization fixtures so the hand-written response models are tested
against the shapes the API actually returns.
"""

from __future__ import annotations

from typing import Any

KEY_INFO: dict[str, Any] = {
    "valid": True,
    "id": "key_abc123",
    "remaining_credits": 99.5,
    "next_reset_at": "2026-02-12T17:48:25.199Z",
    "max_requests_per_seconds": 5,
    "allowed_apis": ["/enrichment/email", "/search/people"],
    "active_plans": [
        {"name": "Unlimited Leads", "status": "active", "started_at": "2026-01-12T17:48:25.200Z"}
    ],
}

_PERSON: dict[str, Any] = {
    "first_name": "Beulah",
    "last_name": "Lee",
    "full_name": "Beulah Lee",
    "nickname": None,
    "civility_title": None,
    "headline": "Software Engineer at Google",
    "about_me": "Motivated engineer.",
    "location": {
        "city": "Sunnyvale",
        "state_code": "CA",
        "country_code": "US",
        "continent": "North America",
    },
    "linkedin_url": "https://www.linkedin.com/in/beulah-lee",
    "connections_count": 500,
    "profile_picture_url": "https://media.licdn.com/dms/image/v2/photo",
    "experiences": [
        {
            "company_name": "Google",
            "job_title": "Software Engineer",
            "company_linkedin_url": "https://www.linkedin.com/company/google",
            "company_linkedin_id": "c346a3f2-6914-51e8-bb11-7da93440a3c0",
            "company_domain": "google.com",
            "job_description": "Google Workspace",
            "job_start_date": "2025-04-01",
            "job_end_date": None,
            "job_is_current": True,
            "job_location": {"city": "Sunnyvale", "state_code": "CA", "country_code": "US"},
        }
    ],
    "education": [
        {"degree": "Bachelor's degree", "start_date": "2019-01-01", "end_date": "2023-01-01"}
    ],
    "skills": ["python"],
    "certifications": [
        {"authority": "Google", "name": "Cloud Cybersecurity", "url": "https://example.com/badge"}
    ],
}

_COMPANY: dict[str, Any] = {
    "linkedin_url": "https://www.linkedin.com/company/google",
    "linkedin_id": 1441,
    "name": "Google",
    "about": "A problem isn't solved until it's solved for all.",
    "specialties": ["search", "cloud"],
    "industry": "Software Development",
    "type": "Public Company",
    "size": "10001+",
    "employees_on_linkedin": 328177,
    "followers": 40093219,
    "founded_year": None,
    "hq": {
        "city": "Mountain View",
        "state": "California",
        "country_code": "US",
        "country_name": "United States",
        "region": "NORAM",
        "continent": "North America",
    },
    "domain": "google.com",
    "website": "https://www.google.com",
}

PEOPLE_SEARCH: dict[str, Any] = {
    "total_results": 14337505,
    "results": [_PERSON],
    "results_length": 1,
    "max_results": 1,
    "cursor": "eyJzIjpbNTAwXX0",
}

COMPANY_SEARCH: dict[str, Any] = {
    "total_results": 100,
    "results": [_COMPANY],
    "results_length": 1,
    "max_results": 1,
    "cursor": "eyJpIjoiY2E5OTcxZjU",
}

EMPLOYEE_FINDER: dict[str, Any] = {
    "company_linkedin_url": "https://www.linkedin.com/company/openai",
    "max_results": 1,
    "results_length": 1,
    "page": 1,
    "total_pages": 1285,
    "results": [_PERSON],
}

WATERFALL_ICP: dict[str, Any] = {
    "company_linkedin_url": "https://www.linkedin.com/company/openai",
    "max_results": 1,
    "results_length": 1,
    "results": [{"icp": 1, "ranking": 1, "person": _PERSON}],
}

EMAIL_ENRICHMENT: dict[str, Any] = {
    "found": True,
    "email": "antoine@blitz-agency.com",
    "all_emails": [
        {
            "email": "antoine@blitz-agency.com",
            "job_order_in_profile": 1,
            "company_linkedin_url": "https://www.linkedin.com/company/blitz-api",
            "email_domain": "blitz-agency.com",
        }
    ],
}

PHONE_ENRICHMENT: dict[str, Any] = {"found": True, "phone": "+1234567890"}

EMAIL_TO_PERSON: dict[str, Any] = {"found": True, "person": _PERSON}

PHONE_TO_PERSON: dict[str, Any] = {"found": True, "person": _PERSON}

COMPANY_ENRICHMENT: dict[str, Any] = {"found": True, "company": _COMPANY}

DOMAIN_TO_LINKEDIN: dict[str, Any] = {
    "found": True,
    "company_linkedin_url": "https://www.linkedin.com/company/blitz-api",
}

LINKEDIN_TO_DOMAIN: dict[str, Any] = {"found": True, "email_domain": "blitz-agency.com"}

CURRENT_DATE: dict[str, Any] = {
    "datetime": "2026-01-08 12:00:00 -05:00",
    "timestamp": 1736385600,
    "timezone": "America/New_York",
    "timezone_name": "(GMT-05:00) New York",
}

EMPLOYMENT_DISTRIBUTION: dict[str, Any] = {
    "company_linkedin_url": "https://www.linkedin.com/company/openai",
    "total_employees": 1234,
    "distribution": [
        {"country": "US", "count": 900},
        {"country": "unknown", "count": 54},
    ],
}

# --- Multi-page fixtures for pagination tests -------------------------------------

# Cursor-based: page 1 returns a cursor; page 2 returns cursor=null (last page).
PEOPLE_SEARCH_PAGE1: dict[str, Any] = {
    "total_results": 2,
    "results": [{**_PERSON, "full_name": "Person One"}],
    "results_length": 1,
    "max_results": 1,
    "cursor": "next-cursor",
}
PEOPLE_SEARCH_PAGE2: dict[str, Any] = {
    "total_results": 2,
    "results": [{**_PERSON, "full_name": "Person Two"}],
    "results_length": 1,
    "max_results": 1,
    "cursor": None,
}

# Page-number-based: page 1 of 2, then page 2 of 2 (last page).
EMPLOYEE_FINDER_PAGE1: dict[str, Any] = {
    "company_linkedin_url": "https://www.linkedin.com/company/openai",
    "max_results": 1,
    "results_length": 1,
    "page": 1,
    "total_pages": 2,
    "results": [{**_PERSON, "full_name": "Employee One"}],
}
EMPLOYEE_FINDER_PAGE2: dict[str, Any] = {
    "company_linkedin_url": "https://www.linkedin.com/company/openai",
    "max_results": 1,
    "results_length": 1,
    "page": 2,
    "total_pages": 2,
    "results": [{**_PERSON, "full_name": "Employee Two"}],
}
