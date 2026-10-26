"""Response models shared across multiple Blitz API endpoints.

These mirror the JSON the API returns. Field shapes vary slightly between
endpoints — e.g. ``Location`` carries ``continent``/``postal_code``/``street_address``
on a person but not on an ``Experience.job_location`` — so divergent fields are modeled
as ``Optional`` on a single superset type rather than duplicated.

Audited field-by-field against the live spec on 2026-10-15. Every field here is one the
spec returns at some site, except the deliberate extras recorded in ``docs/CONTEXT.md`` §7
(``HQ.postcode`` / ``HQ.street``).
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
    "MxRecord",
    "Company",
]


class Location(BlitzModel):
    """A geographic location attached to a person or a job.

    One superset model over three differently-sized spec sites: a person's ``location``
    carries every field; ``Experience.job_location`` has only ``city`` / ``state_code`` /
    ``country_code``; a job's ``location`` (``jobs.*``) has only ``city`` / ``country_code``.
    A field the site doesn't list reads ``None``. That is deliberate — see
    ``docs/CONTEXT.md`` §7.
    """

    city: str | None = None
    state_code: str | None = None
    country_code: str | None = None
    continent: str | None = None
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
    #: Built from the first entry of ``experiences`` (the matched position on the searches)
    #: as ``"<job title> | @<employer>"``, not the free-text headline on the LinkedIn profile.
    headline: str | None = None
    about_me: str | None = None
    location: Location | None = None
    linkedin_url: str | None = None
    connections_count: int | None = None
    #: Always ``None`` since 2026-09-15; the API keeps the key so clients don't break.
    profile_picture_url: str | None = None
    #: Positions from the person's profile. ``search.people``, ``search.employee_finder`` and
    #: ``search.waterfall_icp`` return exactly one: the position that matched, which can be a
    #: past one with ``include_past_jobs`` (read ``job_is_current``). ``enrichment.person``,
    #: ``enrichment.email_to_person`` and ``enrichment.phone_to_person`` return the whole
    #: career, in profile order.
    experiences: BlitzList[Experience] = []
    education: BlitzList[Education] = []
    skills: BlitzList[str] = []
    certifications: BlitzList[Certification] = []


class HQ(BlitzModel):
    """A company's headquarters location.

    .. note::
       ``postcode`` and ``street`` are deliberate extras. The live spec types every ``hq``
       object — on ``search.companies``, ``enrichment.company`` and both TAM builders alike —
       with exactly the six other fields, ``additionalProperties: false`` and all six
       ``required``, so these two read ``None`` on every response. They are kept on purpose:
       they shipped in a released version, and a ``None`` is harmless where an
       ``AttributeError`` would not be. See ``docs/CONTEXT.md`` §7. Do not add *other* fields
       here without checking the live spec first.
    """

    city: str | None = None
    state: str | None = None
    country_code: str | None = None
    country_name: str | None = None
    region: str | None = None
    continent: str | None = None
    #: Not in the live spec — a deliberate extra, see the class note.
    postcode: str | None = None
    #: Not in the live spec — a deliberate extra, see the class note.
    street: str | None = None


class MxRecord(BlitzModel):
    """One MX record of a domain: a mail host and its priority.

    A lower ``priority`` is tried first. Returned in :attr:`Company.mx` and in the ``mx`` of
    ``enrichment.email``.
    """

    priority: int | None = None
    host: str | None = None


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
    #: MX records of ``domain``, lowest priority first, at most 10. **``None`` and ``[]`` mean
    #: different things:** ``None`` is "no MX data for the domain yet", ``[]`` is "the domain
    #: takes no mail". That is why this is not a ``BlitzList``, which would coerce ``None`` to
    #: ``[]`` and erase the difference (``docs/CONTEXT.md`` §5). Returned by
    #: ``enrichment.company`` only, so it is ``None`` on every other endpoint's companies.
    mx: list[MxRecord] | None = None
