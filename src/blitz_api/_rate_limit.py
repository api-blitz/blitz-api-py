"""Client-side rate limiters: re-exports the async source and its generated sync twin.

The implementations live in ``_rate_limit_async.py`` (hand-written source) and
``_rate_limit_sync.py`` (generated from it by ``scripts/gen_sync.py``); this module just
re-exports both so ``from blitz_api._rate_limit import RateLimiter`` keeps working —
mirroring how ``_client.py`` re-exports the two clients.
"""

from __future__ import annotations

from ._rate_limit_async import AsyncRateLimiter
from ._rate_limit_sync import RateLimiter

__all__ = ["AsyncRateLimiter", "RateLimiter"]
