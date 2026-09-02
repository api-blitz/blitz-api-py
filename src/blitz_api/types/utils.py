"""Response models for the Utilities resource."""

from __future__ import annotations

from ._models import BlitzResponse

__all__ = [
    "CurrentDateResponse",
]


class CurrentDateResponse(BlitzResponse):
    """Result of ``utils.current_date``."""

    datetime: str | None = None
    timestamp: int | None = None
    timezone: str | None = None
    timezone_name: str | None = None
