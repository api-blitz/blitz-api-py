"""Response models for the Changelog resource.

``changelog.list`` returns a **top-level JSON array** of entries, so the payload is
modelled as a pydantic ``RootModel`` (:data:`ChangelogResponse`) that the request
pipeline can validate; the resource method unwraps it to a plain
``list[ChangelogEntry]`` (``.root``).
"""

from __future__ import annotations

from pydantic import RootModel, field_validator

from ._models import BlitzModel, null_list_to_empty

__all__ = [
    "ChangelogLink",
    "ChangelogEntry",
    "ChangelogResponse",
]


class ChangelogLink(BlitzModel):
    """A labelled external link attached to a changelog entry (docs, migration guide, ...)."""

    label: str | None = None
    url: str | None = None


class ChangelogEntry(BlitzModel):
    """A single public changelog entry, newest-first in the list.

    ``type`` is the impact category — one of ``breaking``, ``feature``, ``improvement``,
    ``fix``, ``deprecation``, ``announcement`` — kept a **loose ``str``** (not an enum)
    so a new upstream category never breaks deserialization, the same forward-compatible
    posture as ``Company.type`` / ``Company.industry``. ``affected_endpoints`` and
    ``links`` are omitted for product announcements.
    """

    date: str | None = None
    type: str | None = None
    title: str | None = None
    body: str | None = None
    affected_endpoints: list[str] = []
    links: list[ChangelogLink] = []

    # The API returns ``null`` (not ``[]``) for an empty list; coerce to ``[]``.
    _empty_lists = field_validator("affected_endpoints", "links", mode="before")(null_list_to_empty)


#: The ``changelog.list`` payload: a top-level array of entries. ``changelog.list``
#: unwraps this ``RootModel`` to the plain ``list[ChangelogEntry]`` it returns (``.root``).
ChangelogResponse = RootModel[list[ChangelogEntry]]
