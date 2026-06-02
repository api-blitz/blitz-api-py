"""Type aliases that differ between the async source and the generated sync code.

The async client takes an awaitable sleep callable; the sync client takes a plain
one. ``scripts/gen_sync.py`` rewrites the token ``AsyncSleep`` to ``SyncSleep`` when
it transliterates the async source, so both flavours stay precisely typed without the
generator having to rewrite a subscripted generic (which token-level renaming can't do).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    import httpx

#: Sleep callable accepted by ``AsyncBlitzAPI`` (e.g. ``asyncio.sleep``).
AsyncSleep = Callable[[float], Awaitable[None]]

#: Sleep callable accepted by ``BlitzAPI`` (e.g. ``time.sleep``).
SyncSleep = Callable[[float], None]

#: Per-call timeout override: a number of seconds, an :class:`httpx.Timeout`, or
#: ``None`` to fall back to the client-wide timeout. (Defined with ``Union`` and a
#: forward reference so importing it never forces ``httpx`` to load at runtime.)
TimeoutParam = Union[float, "httpx.Timeout", None]
