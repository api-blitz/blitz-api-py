"""Response models for the Account resource."""

from __future__ import annotations

from typing import Literal

from ._models import BlitzModel

__all__ = ["ActivePlan", "KeyInfo"]


class ActivePlan(BlitzModel):
    """A subscription plan attached to the API key."""

    name: str | None = None
    status: str | None = None
    started_at: str | None = None


class KeyInfo(BlitzModel):
    """The result of ``client.account.key_info()`` — key health and limits."""

    valid: bool | None = None
    id: str | None = None
    # A number on metered plans; the literal "unlimited" on unlimited plans.
    remaining_credits: float | Literal["unlimited"] | None = None
    next_reset_at: str | None = None
    max_requests_per_seconds: float | Literal["unlimited"] | None = None
    allowed_apis: list[str] = []
    active_plans: list[ActivePlan] = []
