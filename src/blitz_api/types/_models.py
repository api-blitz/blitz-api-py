"""Base Pydantic model for every Blitz API response type."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BlitzModel(BaseModel):
    """Base for all response models.

    Configured to be forward-compatible: unknown fields returned by the API are
    preserved (reachable via :attr:`model_extra`) instead of raising, so a new
    server-side field never breaks deserialization. Known fields stay precisely
    typed.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        # The API exposes fields like ``max_requests_per_seconds``; silence the
        # ``model_`` protected-namespace warnings without affecting behaviour.
        protected_namespaces=(),
    )
