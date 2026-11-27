"""Response models for the Account resource."""

from __future__ import annotations

from typing import Literal

from ._models import BlitzModel, BlitzResponse

__all__ = ["ActivePlan", "KeyInfo", "SearchLimit"]


class ActivePlan(BlitzModel):
    """A subscription plan attached to the API key."""

    name: str | None = None
    status: str | None = None
    started_at: str | None = None


class SearchLimit(BlitzModel):
    """The result limits of one search endpoint, an entry of ``KeyInfo.limits``."""

    # The endpoint this limit applies to, in the format of ``allowed_apis`` (no ``/v2`` prefix).
    path: str | None = None
    # The largest ``max_results`` one call to this endpoint accepts; a larger value returns 422.
    max_results_per_page: float | None = None
    # The most results one search returns across all its pages. A search that gets to this
    # number ends with a ``None`` cursor (or its last ``page``). A number, or "unlimited".
    max_results_total: float | Literal["unlimited"] | None = None


class KeyInfo(BlitzResponse):
    """The result of ``client.account.key_info()`` — key health and limits."""

    valid: bool | None = None
    id: str | None = None
    # A number on metered plans; the literal "unlimited" on unlimited plans.
    # Renamed by the API on 2026-09-01 to match ``fair_usage.records_remaining``
    # and the ``x-records-remaining`` response header.
    records_remaining: float | Literal["unlimited"] | None = None
    next_reset_at: str | None = None
    max_requests_per_seconds: float | Literal["unlimited"] | None = None
    # The result limits of each search endpoint (added by the API on 2026-11-27).
    limits: list[SearchLimit] = []
    allowed_apis: list[str] = []
    active_plans: list[ActivePlan] = []
