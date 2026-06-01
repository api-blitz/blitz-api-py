"""Response models for the Account resource."""

from __future__ import annotations

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
    remaining_credits: float | None = None
    next_reset_at: str | None = None
    max_requests_per_seconds: int | None = None
    allowed_apis: list[str] = []
    active_plans: list[ActivePlan] = []
