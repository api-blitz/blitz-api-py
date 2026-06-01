"""Response models shared across multiple Blitz API endpoints.

These mirror the JSON the API returns. Field shapes vary slightly between
endpoints (e.g. ``Experience.company_name`` is only populated by people search,
``HQ.postcode``/``street`` only by company enrichment), so divergent fields are
modeled as ``Optional`` on a single superset type rather than duplicated.
"""

from __future__ import annotations

from ._models import BlitzModel

__all__ = [
    "Location",
    "Experience",
    "Education",
    "Certification",
    "Person",
    "HQ",
    "Company",
]


class Location(BlitzModel):
    """A geographic location attached to a person or a job."""

    city: str | None = None
    state_code: str | None = None
    country_code: str | None = None
    continent: str | None = None


class Experience(BlitzModel):
    """A single role from a person's work history."""

    job_title: str | None = None
    # Populated by ``search.people``; absent from employee-finder / reverse lookups.
    company_name: str | None = None
    company_linkedin_url: str | None = None
    company_linkedin_id: str | None = None
    company_domain: str | None = None
    job_description: str | None = None
    job_start_date: str | None = None
    job_end_date: str | None = None
    job_is_current: bool | None = None
    job_location: Location | None = None


class Education(BlitzModel):
    """A single education entry from a person's profile."""

    school: str | None = None
    degree: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class Certification(BlitzModel):
    """A professional certification listed on a person's profile."""

    authority: str | None = None
    name: str | None = None
    url: str | None = None


class Person(BlitzModel):
    """A person profile returned by search and reverse-enrichment endpoints."""

    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    nickname: str | None = None
    civility_title: str | None = None
    headline: str | None = None
    about_me: str | None = None
    location: Location | None = None
    linkedin_url: str | None = None
    connections_count: int | None = None
    profile_picture_url: str | None = None
    experiences: list[Experience] = []
    education: list[Education] = []
    skills: list[str] = []
    certifications: list[Certification] = []


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
