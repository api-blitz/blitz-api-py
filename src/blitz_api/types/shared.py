"""Response models shared across multiple Blitz API endpoints.

These mirror the JSON the API returns. Field shapes vary slightly between
endpoints (e.g. ``Experience.company_name`` is only populated by people search,
``HQ.postcode``/``street`` only by company enrichment), so divergent fields are
modeled as ``Optional`` on a single superset type rather than duplicated.
"""

from __future__ import annotations

from ._models import BlitzList, BlitzModel

__all__ = [
    "Location",
    "Experience",
    "Education",
    "Certification",
    "Person",
    "HQ",
    "EmployeeGrowth",
    "Company",
]


class Location(BlitzModel):
    """A geographic location attached to a person or a job."""

    city: str | None = None
    state_code: str | None = None
    country_code: str | None = None
    continent: str | None = None
    # Populated on a person's ``location``; absent from ``Experience.job_location``.
    postal_code: str | None = None
    street_address: str | None = None


class Experience(BlitzModel):
    """A single role from a person's work history."""

    job_title: str | None = None
    # Prefers the name on the linked LinkedIn company page when there is one.
    company_name: str | None = None
    company_linkedin_url: str | None = None
    company_linkedin_id: str | None = None
    # Filled on past positions as well as the current one.
    company_domain: str | None = None
    job_description: str | None = None
    job_start_date: str | None = None
    job_end_date: str | None = None
    job_is_current: bool | None = None
    #: How the role is contracted, e.g. ``"Full-time"``, ``"Contract"``, ``"Internship"``.
    job_contract_type: str | None = None
    #: Where the work is performed, e.g. ``"Remote"``, ``"Hybrid"``, ``"On-site"``.
    job_work_arrangement: str | None = None
    job_location: Location | None = None


class Education(BlitzModel):
    """A single education entry from a person's profile.

    The field of study is part of ``degree`` (e.g. ``"Bachelor of Science, Industrial
    Engineering"``); the API removed the separate ``field_of_study`` field on
    2026-09-15.
    """

    school_name: str | None = None
    degree: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class Certification(BlitzModel):
    """A professional certification listed on a person's profile."""

    authority: str | None = None
    name: str | None = None
    url: str | None = None


class Person(BlitzModel):
    """A person profile returned by search and enrichment endpoints."""

    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    nickname: str | None = None
    civility_title: str | None = None
    #: Built from the person's first position as ``"<job title> | @<employer>"``, not
    #: the free-text headline written on the LinkedIn profile.
    headline: str | None = None
    about_me: str | None = None
    location: Location | None = None
    linkedin_url: str | None = None
    connections_count: int | None = None
    #: Always ``None`` since 2026-09-15; the API keeps the key so clients don't break.
    profile_picture_url: str | None = None
    #: Every position the person has held, in profile order.
    experiences: BlitzList[Experience] = []
    education: BlitzList[Education] = []
    skills: BlitzList[str] = []
    certifications: BlitzList[Certification] = []


class HQ(BlitzModel):
    """A company's headquarters location.

    Company enrichment returns ``postcode`` and ``street`` in addition to the
    fields company search returns; both are optional here.
    """

    city: str | None = None
    state: str | None = None
    postcode: str | None = None
    country_code: str | None = None
    country_name: str | None = None
    region: str | None = None
    continent: str | None = None
    street: str | None = None


class EmployeeGrowth(BlitzModel):
    """Headcount growth over one window, e.g. ``{percentage: 12.5, timespan: "1 year"}``."""

    percentage: float | None = None
    timespan: str | None = None


class Company(BlitzModel):
    """A company profile returned by company search and company enrichment."""

    linkedin_url: str | None = None
    linkedin_id: int | None = None
    name: str | None = None
    about: str | None = None
    specialties: list[str] | None = None
    industry: str | None = None
    type: str | None = None
    size: str | None = None
    employees_on_linkedin: int | None = None
    followers: int | None = None
    founded_year: int | None = None
    hq: HQ | None = None
    domain: str | None = None
    website: str | None = None
    #: The company's tagline, as shown on its LinkedIn page.
    slogan: str | None = None
    #: Estimated annual revenue in USD.
    revenue: float | None = None
    #: Headcount growth, one entry per reported window.
    employee_growth: BlitzList[EmployeeGrowth] = []
