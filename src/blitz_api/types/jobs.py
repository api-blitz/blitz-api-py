"""Response models for the Jobs resource.

``jobs.search``/``jobs.company`` return ``CursorPage[Job]`` (the auto-paging cursor
page defined in :mod:`blitz_api._pagination_async` / ``_pagination_sync``), so there
is no per-endpoint response wrapper here — only the ``Job`` item model.
"""

from __future__ import annotations

from ._models import BlitzModel
from .shared import Location

__all__ = [
    "Job",
]


class Job(BlitzModel):
    """A single job posting returned by ``jobs.search`` and ``jobs.company``.

    ``date_posted`` is the raw timestamp string the API emits (e.g.
    ``"2026-07-08 23:00:07+02"`` — a space separator and a UTC offset, not ISO-8601),
    so it is kept as a string rather than parsed to a ``datetime``. ``location`` reuses
    the shared :class:`~blitz_api.types.shared.Location` model, of which the jobs payload
    populates ``city`` and ``country_code``.
    """

    date_posted: str | None = None
    title: str | None = None
    url: str | None = None
    company_name: str | None = None
    company_linkedin_url: str | None = None
    ai_summary: str | None = None
    location: Location | None = None
