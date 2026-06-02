"""The public Blitz API clients: :class:`BlitzAPI` (sync) and :class:`AsyncBlitzAPI`.

The async client is hand-written in :mod:`blitz_api._client_async`; the sync client in
:mod:`blitz_api._client_sync` is generated from it by ``scripts/gen_sync.py``. This module
re-exports both so ``from blitz_api._client import BlitzAPI`` keeps working.
"""

from __future__ import annotations

from ._client_async import AsyncBlitzAPI
from ._client_sync import BlitzAPI

__all__ = ["AsyncBlitzAPI", "BlitzAPI"]
