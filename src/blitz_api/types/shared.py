"""Response models shared across multiple Blitz API endpoints.

These mirror the JSON the API returns. Field shapes vary slightly between
endpoints — e.g. ``Location`` carries ``continent``/``postal_code``/``street_address``
on a person but not on an ``Experience.job_location`` — so divergent fields are modeled
as ``Optional`` on a single superset type rather than duplicated.

Audited field-by-field against the live spec on 2026-09-22; every field here is one the
spec returns, except the two flagged on :class:`HQ`.
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
    #: Positions from the person's profile, in profile order. **How many** positions land
    #: here depends on the endpoint, and upstream currently contradicts itself for
    #: ``search.people``: the changelog entry of 2026-09-21 says it returns only the
    #: position that matched your filters, while the docs still say the whole career.
    #: ``enrichment.person`` returns the whole career either way. Read ``job_is_current``
    #: rather than assuming index 0 is the current role.
    experiences: BlitzList[Experience] = []
    education: BlitzList[Education] = []
    skills: BlitzList[str] = []
    certifications: BlitzList[Certification] = []


class HQ(BlitzModel):
    """A company's headquarters location.

    .. warning::
       ``postcode`` and ``street`` are **unverified**. They predate the spec publishing
       real response properties, and the live spec now types every ``hq`` object — on
       ``search.companies``, ``enrichment.company`` and both TAM builders alike — with
       exactly the six other fields, ``additionalProperties: false`` and all six
       ``required``. A closed schema cannot carry them, so they read ``None`` on every
       response. Kept pending confirmation from the API owner; see ``docs/CONTEXT.md``
       §7. Do not add fields here without checking the live spec first.
    """

    city: str | None = None
    state: str | None = None
    country_code: str | None = None
    country_name: str | None = None
    region: str | None = None
    continent: str | None = None
    #: Unverified — see the class warning.
    postcode: str | None = None
    #: Unverified — see the class warning.
    street: str | None = None


class Company(BlitzModel):
    """A company profile returned by company search and company enrichment."""

    linkedin_url: str | None = None
    linkedin_id: int | None = None
    name: str | None = None
    about: str | None = None
    specialties: BlitzList[str] = []
    industry: str | None = None
    type: str | None = None
    size: str | None = None
    employees_on_linkedin: int | None = None
    followers: int | None = None
    founded_year: int | None = None
    hq: HQ | None = None
    domain: str | None = None
    website: str | None = None
