"""Response models for the Identity resource."""

from __future__ import annotations

from ._models import BlitzList, BlitzModel, BlitzResponse
from .shared import HQ, Location

__all__ = [
    "MatchPastExperience",
    "PersonMatch",
    "PersonMatchResponse",
    "CompanyMatch",
    "CompanyMatchResponse",
]


class MatchPastExperience(BlitzModel):
    """A past job of a matched person: the company and the job title."""

    company_name: str | None = None
    job_title: str | None = None


class PersonMatch(BlitzModel):
    """A person that ``identity.person_match`` returns, in ``match`` or in ``candidates``."""

    linkedin_url: str | None = None
    full_name: str | None = None
    #: Title of the current job. With several current jobs, the one at the company of the input.
    job_title: str | None = None
    #: Company of that job.
    company_name: str | None = None
    location: Location | None = None
    #: Probability that this is the right person, from 0 to 1.
    confidence: float | None = None
    #: The 3 latest past jobs, and the job at the company of the input when it is an older one.
    past_experiences: BlitzList[MatchPastExperience] = []


class PersonMatchResponse(BlitzResponse):
    """Result of ``identity.person_match``.

    ``status`` is ``matched`` (use ``match``), ``ambiguous`` (choose among ``candidates``) or
    ``not_found`` (0 records). It is a loose ``str``, not an enum, so a new value never breaks
    parsing, the same posture as ``ChangelogEntry.type``. ``match`` is ``None`` unless
    ``status`` is ``matched``; ``candidates`` lists up to 10 other plausible people
    (confidence of 0.3 or more), most probable first.
    """

    status: str | None = None
    match: PersonMatch | None = None
    candidates: BlitzList[PersonMatch] = []


class CompanyMatch(BlitzModel):
    """A company that ``identity.company_match`` returns, in ``match`` or in ``candidates``."""

    linkedin_url: str | None = None
    name: str | None = None
    domain: str | None = None
    industry: str | None = None
    #: Employee range, such as ``51-200``.
    size: str | None = None
    #: Headquarters of the company.
    location: HQ | None = None
    #: Probability that this is the right company, from 0 to 1.
    confidence: float | None = None


class CompanyMatchResponse(BlitzResponse):
    """Result of ``identity.company_match``.

    ``status`` is ``matched`` (use ``match``), ``ambiguous`` (choose among ``candidates``) or
    ``not_found`` (0 records), as a loose ``str`` (see :class:`PersonMatchResponse`).
    ``candidates`` lists up to 10 other plausible companies (confidence of 0.3 or more), most
    probable first. With a ``company_domain`` alone that several pages share, the pages of the
    domain are listed, also under 0.3, with a confidence of 0.8 at most.
    """

    status: str | None = None
    match: CompanyMatch | None = None
    candidates: BlitzList[CompanyMatch] = []
