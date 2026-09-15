"""Base Pydantic models shared by every Blitz API response type.

:class:`BlitzModel` is the forward-compatible base every model inherits.
:class:`BlitzResponse` adds the ``fair_usage`` envelope that every ``/v2`` endpoint
returns alongside its payload, so only *top-level* response models (and the
pagination page classes) carry it — nested entities like ``Person`` do not.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypeVar

from pydantic import BaseModel, BeforeValidator, ConfigDict


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


class FairUsageRateLimit(BlitzModel):
    """The rate-limit slice of :class:`FairUsage`.

    Absent on endpoints that are not rate limited (notably ``account.key_info``).
    """

    # Modelled as ``float`` for the same reason as ``KeyInfo.max_requests_per_seconds``:
    # the spec types it as a plain JSON number.
    requests_per_second: float | None = None
    remaining_this_second: int | None = None


class FairUsage(BlitzModel):
    """Record usage, rate limit, and tracing data for a single request.

    Returned by every ``/v2`` endpoint on success, and on the ``402``
    insufficient-balance error (:attr:`~blitz_api.APIStatusError.fair_usage`).
    """

    #: Records this request consumed, after reconciliation against the results
    #: actually returned.
    records_used: int | None = None
    #: Records left on the plan after this request. A number on metered plans; the
    #: literal ``"unlimited"`` on unlimited plans.
    records_remaining: float | Literal["unlimited"] | None = None
    #: When the record balance resets. ``None`` on an unlimited plan.
    next_reset_at: str | None = None
    #: ``None`` on endpoints that are not rate limited.
    rate_limit: FairUsageRateLimit | None = None
    #: Quote this id when contacting support.
    request_id: str | None = None


class BlitzResponse(BlitzModel):
    """Base for top-level response models: the payload plus the ``fair_usage`` block.

    ``fair_usage`` is ``None`` on the public ``/changelog/`` endpoint (which is not
    metered) and on any response predating the API's 2026-08-31 rollout.
    """

    fair_usage: FairUsage | None = None


_ItemT = TypeVar("_ItemT")


def _null_to_empty(value: Any) -> Any:
    return [] if value is None else value


#: A list field the API may send as ``null`` instead of ``[]``.
#:
#: Many list-valued response fields are ``array | null`` in the spec (a person's
#: ``education`` / ``skills`` / ``certifications``, a company's ``employee_growth``, a
#: changelog entry's ``affected_endpoints`` / ``links``). A plain ``list[T] = []`` field
#: *rejects* ``null``, so those payloads would raise. Declaring the field
#: ``BlitzList[T]`` coerces ``null`` to ``[]`` at parse time, so the attribute is always
#: iterable — the TS SDK's ``blitzList``, expressed in the type rather than in a
#: separate validator that has to name its fields as strings.
BlitzList = Annotated[list[_ItemT], BeforeValidator(_null_to_empty)]
