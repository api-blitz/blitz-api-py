"""Canonical example response payloads, mirroring the Blitz OpenAPI v2 examples.

Used as deserialization fixtures so the hand-written response models are tested
against the shapes the API actually returns.
"""

from __future__ import annotations

from typing import Any

# The ``fair_usage`` envelope every /v2 endpoint returns alongside its payload.
FAIR_USAGE: dict[str, Any] = {
    "records_used": 3,
    "records_remaining": 9913547,
    "next_reset_at": "2026-09-29T10:25:23.155Z",
    "rate_limit": {"requests_per_second": 100, "remaining_this_second": 97},
    "request_id": "019bae09-0055-7441-b2ea-16086e499219",
}

# ``key-info`` is not rate limited, so its ``fair_usage`` block carries no ``rate_limit``.
KEY_INFO: dict[str, Any] = {
    "valid": True,
    "id": "key_abc123",
    "records_remaining": 99.5,
    "next_reset_at": "2026-02-12T17:48:25.199Z",
    "max_requests_per_seconds": 5,
    "allowed_apis": ["/enrichment/email", "/search/people"],
    "active_plans": [
        {"name": "Unlimited Leads", "status": "active", "started_at": "2026-01-12T17:48:25.200Z"}
    ],
    "fair_usage": {
        "records_used": 0,
        "records_remaining": 99.5,
        "next_reset_at": "2026-02-12T17:48:25.199Z",
        "request_id": "019bae09-0055-7441-b2ea-16086e499219",
    },
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
        "postal_code": "94089",
        "street_address": "1600 Amphitheatre Parkway",
    },
    "linkedin_url": "https://www.linkedin.com/in/beulah-lee",
    "connections_count": 500,
    # Always null since 2026-09-15; the API keeps the key so clients don't break.
    "profile_picture_url": None,
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
            "job_contract_type": "Full-time",
            "job_work_arrangement": "Hybrid",
            "job_location": {"city": "Sunnyvale", "state_code": "CA", "country_code": "US"},
        },
        {
            "company_name": "Stripe",
            "job_title": "Backend Engineer",
            "company_linkedin_url": "https://www.linkedin.com/company/stripe",
            "company_linkedin_id": "6f0b1c53-2b4a-4a2e-9f55-1d3a2f1b7c88",
            "company_domain": "stripe.com",
            "job_description": None,
            "job_start_date": "2023-02-01",
            "job_end_date": "2025-03-01",
            "job_is_current": False,
            "job_contract_type": "Full-time",
            "job_work_arrangement": "Remote",
            "job_location": {"city": "San Francisco", "state_code": "CA", "country_code": "US"},
        },
    ],
    # The API folded the old ``field_of_study`` into ``degree`` on 2026-09-15.
    "education": [
        {
            "school_name": "Stanford University",
            "degree": "Bachelor of Science, Computer Science",
            "start_date": "2019-01-01",
            "end_date": "2023-01-01",
        }
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
    "slogan": "Organize the world's information.",
    "revenue": 307394000000.0,
    "employee_growth": [{"percentage": 12.5, "timespan": "1 year"}],
}

# A person whose optional list fields come back as ``null`` rather than ``[]``.
PERSON_NULL_LISTS: dict[str, Any] = {
    **_PERSON,
    "experiences": None,
    "education": None,
    "skills": None,
    "certifications": None,
}

# A company whose ``employee_growth`` comes back as ``null``.
COMPANY_NULL_GROWTH: dict[str, Any] = {**_COMPANY, "employee_growth": None}

PEOPLE_SEARCH: dict[str, Any] = {
    "total_results": 14337505,
    "results": [_PERSON],
    "results_length": 1,
    "max_results": 1,
    "cursor": "example_cursor_people_p2",
    "fair_usage": FAIR_USAGE,
}

COMPANY_SEARCH: dict[str, Any] = {
    "total_results": 100,
    "results": [_COMPANY],
    "results_length": 1,
    "max_results": 1,
    "cursor": "example_cursor_companies_p2",
}

EMPLOYEE_FINDER: dict[str, Any] = {
    "company_linkedin_url": "https://www.linkedin.com/company/openai",
    "max_results": 1,
    "results_length": 1,
    "page": 1,
    "total_pages": 1285,
    "results": [_PERSON],
}

_JOB: dict[str, Any] = {
    "date_posted": "2026-07-08 23:00:07+02",
    "title": "Growth Marketing Manager, SMB Ads",
    "url": "https://www.linkedin.com/jobs/view/growth-marketing-manager-smb-ads-at-openai-4437309737",
    "company_name": "OpenAI",
    "company_linkedin_url": "https://www.linkedin.com/company/openai",
    "ai_summary": (
        "The Growth Marketing Manager will execute growth experiments across "
        "acquisition, activation, lifecycle, and early retention for small business "
        "advertisers."
    ),
    "location": {"city": "San Francisco", "country_code": "US"},
}

JOB_SEARCH: dict[str, Any] = {
    "total_results": 4821,
    "results": [_JOB],
    "results_length": 1,
    "max_results": 1,
    "cursor": "example_cursor_jobs_p2",
}

COMPANY_JOBS: dict[str, Any] = {
    "total_results": 37,
    "results": [_JOB],
    "results_length": 1,
    "max_results": 1,
    "cursor": "example_cursor_company_jobs_p2",
}

WATERFALL_ICP: dict[str, Any] = {
    "company_linkedin_url": "https://www.linkedin.com/company/openai",
    "max_results": 1,
    "results_length": 1,
    "results": [{"icp": 1, "ranking": 1, "person": _PERSON}],
}

PERSON_ENRICHMENT: dict[str, Any] = {
    "found": True,
    "person": _PERSON,
    "fair_usage": FAIR_USAGE,
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

PHONE_ENRICHMENT: dict[str, Any] = {
    "found": True,
    "phone": "+1234567890",
    "fair_usage": FAIR_USAGE,
}

EMAIL_TO_PERSON: dict[str, Any] = {"found": True, "person": _PERSON}

PHONE_TO_PERSON: dict[str, Any] = {"found": True, "person": _PERSON}

COMPANY_ENRICHMENT: dict[str, Any] = {"found": True, "company": _COMPANY}

DOMAIN_TO_LINKEDIN: dict[str, Any] = {
    "found": True,
    "company_linkedin_url": "https://www.linkedin.com/company/blitz-api",
    "company_name": "Blitz",
    "other": [
        {
            "company_linkedin_url": "https://www.linkedin.com/company/blitz-other",
            "company_name": "Blitz Other",
        }
    ],
}

# An unlimited-plan key: record/rate fields come back as the literal "unlimited".
KEY_INFO_UNLIMITED: dict[str, Any] = {
    "valid": True,
    "id": "key_unlimited",
    "records_remaining": "unlimited",
    "max_requests_per_seconds": "unlimited",
    "allowed_apis": ["/search/people"],
    "active_plans": [{"name": "Unlimited", "status": "active"}],
}

LINKEDIN_TO_DOMAIN: dict[str, Any] = {"found": True, "email_domain": "blitz-agency.com"}

CURRENT_DATE: dict[str, Any] = {
    "datetime": "2026-01-08 12:00:00 -05:00",
    "timestamp": 1736385600,
    "timezone": "America/New_York",
    "timezone_name": "(GMT-05:00) New York",
}

COUNTRY_DISTRIBUTION: dict[str, Any] = {
    "company_linkedin_url": "https://www.linkedin.com/company/openai",
    "total_employees": 1234,
    "distribution": [
        {"country": "US", "count": 900, "percentage_ratio": 72.93},
        {"country": "GB", "count": 200, "percentage_ratio": 16.21},
        {"country": "unknown", "count": 54, "percentage_ratio": 4.38},
    ],
}

DEPARTMENT_DISTRIBUTION: dict[str, Any] = {
    "company_linkedin_url": "https://www.linkedin.com/company/openai",
    "total_employees": 1234,
    "distribution": [
        {"department": "Engineering", "count": 320, "percentage_ratio": 25.93},
        {"department": "Sales", "count": 210, "percentage_ratio": 17.02},
        {"department": "Other", "count": 12, "percentage_ratio": 0.97},
    ],
}

# TAM by jobs: each match is a company plus how many of its live postings matched.
# The envelope carries NO ``total_results`` (the spec omits it for this endpoint).
TAM_BY_JOBS: dict[str, Any] = {
    "results": [{"company": _COMPANY, "matched_jobs": 7}],
    "results_length": 1,
    "max_results": 1,
    "cursor": "example_cursor_tam_p2",
}

# TAM by people: each match is a company plus how many of its employees matched.
# Same envelope as TAM by jobs — no ``total_results``.
TAM_BY_PEOPLE: dict[str, Any] = {
    "results": [{"company": _COMPANY, "matched_people": 27}],
    "results_length": 1,
    "max_results": 1,
    "cursor": "example_cursor_tam_people_p2",
}

# A 402 body: the API attaches the usage block so the caller can see when it resets.
INSUFFICIENT_RECORDS: dict[str, Any] = {
    "success": False,
    "message": (
        "Fair Use limit reached. Upgrade your plan at app.blitz-api.ai/billing or "
        "contact support to increase your monthly capacity."
    ),
    "fair_usage": {
        "records_used": 0,
        "records_remaining": 0,
        "next_reset_at": "2026-09-29T10:25:23.155Z",
        "request_id": "019bae09-0055-7441-b2ea-16086e499219",
    },
}

# Public changelog: a top-level JSON array of entries, newest-first.
CHANGELOG: list[dict[str, Any]] = [
    {
        "date": "2026-08-01",
        "type": "feature",
        "title": "Added the company TAM-by-jobs endpoint",
        "body": "Build a Total Addressable Market of companies from live hiring signals.",
        "affected_endpoints": ["/v2/company/tam-by-jobs"],
        "links": [{"label": "Docs", "url": "https://docs.blitz-api.ai/changelog"}],
    },
    {"date": "2026-07-15", "type": "fix", "title": "Fixed a cursor pagination edge case"},
]

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

# Cursor-based jobs: page 1 returns a cursor; page 2 returns cursor=null (last page).
JOB_SEARCH_PAGE1: dict[str, Any] = {
    "total_results": 2,
    "results": [{**_JOB, "title": "Job One"}],
    "results_length": 1,
    "max_results": 1,
    "cursor": "next-cursor",
}
JOB_SEARCH_PAGE2: dict[str, Any] = {
    "total_results": 2,
    "results": [{**_JOB, "title": "Job Two"}],
    "results_length": 1,
    "max_results": 1,
    "cursor": None,
}

# Cursor-based TAM by people: page 1 returns a cursor; page 2 ends the walk.
TAM_BY_PEOPLE_PAGE1: dict[str, Any] = {
    "results": [{"company": {**_COMPANY, "name": "Company One"}, "matched_people": 27}],
    "results_length": 1,
    "max_results": 1,
    "cursor": "next-cursor",
}
TAM_BY_PEOPLE_PAGE2: dict[str, Any] = {
    "results": [{"company": {**_COMPANY, "name": "Company Two"}, "matched_people": 4}],
    "results_length": 1,
    "max_results": 1,
    "cursor": None,
}
