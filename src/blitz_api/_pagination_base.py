"""Shared base for the auto-paginating page models.

Field-free pagination *state* and the request context needed to fetch the next page
live here (no ``async``, so this file is NOT processed by ``scripts/gen_sync.py``). The
sync vs async iteration surface lives in ``_pagination_async.py`` (source) and
``_pagination_sync.py`` (generated). Both the sync and async clients import
:class:`BasePage` for a single, flavour-neutral ``isinstance`` check when binding context.
"""

from __future__ import annotations

from typing import Any

from pydantic import PrivateAttr

from .types._models import BlitzModel


class BasePage(BlitzModel):
    """Common pagination context. Subclasses add the page fields + iteration."""

    # Bound by the client after a page is parsed, so the page can fetch the next one.
    _client: Any = PrivateAttr(default=None)
    _method: str = PrivateAttr(default="POST")
    _path: str = PrivateAttr(default="")
    _body: dict[str, Any] = PrivateAttr(default_factory=dict)
    # The per-call timeout override the first page was fetched with, so every
    # subsequent auto-paged request honours it too. ``Any`` (rather than
    # ``TimeoutParam``) keeps this module from importing ``httpx`` at runtime.
    _timeout: Any = PrivateAttr(default=None)

    def _bind(
        self,
        client: Any,
        method: str,
        path: str,
        body: dict[str, Any] | None,
        timeout: Any = None,
    ) -> None:
        self._client = client
        self._method = method
        self._path = path
        self._body = dict(body) if body else {}
        self._timeout = timeout

    def has_next_page(self) -> bool:
        """Whether another page is available (overridden per pagination style)."""
        return False

    def _next_body(self) -> dict[str, Any]:
        """The request body for the next page (overridden per pagination style)."""
        raise NotImplementedError
