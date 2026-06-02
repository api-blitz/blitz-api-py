"""Auto-paginating page objects (async source).

The sync versions in ``_pagination_sync.py`` are generated from this file by
``scripts/gen_sync.py`` (it strips ``async``/``await`` and renames the ``Async*`` /
``AsyncIterator`` / ``__aiter__`` tokens). Edit this file, then run the generator.

``search.people``/``search.companies`` return the cursor-based page class and
``search.employee_finder`` the page-number-based one. Both auto-paginate over every item
when iterated (``for``/``async for``), and also expose ``.auto_paging_iter()``,
``.iter_pages()``, and ``.get_next_page()``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Generic, TypeVar, cast

from typing_extensions import Self

from ._exceptions import BlitzError
from ._pagination_base import BasePage

ItemT = TypeVar("ItemT")


class AsyncPaginator(BasePage, Generic[ItemT]):
    """Mixes auto-pagination over items/pages onto a concrete page model."""

    results: list[ItemT] = []

    # ``__iter__`` (the generated sync twin of this) intentionally overrides
    # ``BaseModel.__iter__`` to yield items instead of (field, value) pairs.
    def __aiter__(self) -> AsyncIterator[ItemT]:  # type: ignore[override]
        return self._auto_paging_items()

    async def _auto_paging_items(self, max_items: int | None = None) -> AsyncIterator[ItemT]:
        page = self
        emitted = 0
        while True:
            for item in page.results:
                yield item
                emitted += 1
                if max_items is not None and emitted >= max_items:
                    return
            if not page.has_next_page():
                return
            page = await page._fetch_next()

    def auto_paging_iter(self, *, max_items: int | None = None) -> AsyncIterator[ItemT]:
        """Iterate every item across all pages, optionally stopping after ``max_items``."""
        return self._auto_paging_items(max_items)

    async def collect(self, *, max_items: int | None = None) -> list[ItemT]:
        """Drain every item across all pages into a list, optionally capped at ``max_items``.

        Convenience over a manual iteration loop; pair with ``max_items`` so an unbounded result
        set can't exhaust memory — or credits, since the API bills per result returned.
        """
        items: list[ItemT] = []
        async for item in self._auto_paging_items(max_items):
            items.append(item)
        return items

    async def iter_pages(self, *, max_pages: int | None = None) -> AsyncIterator[Self]:
        """Iterate page objects across the result set, optionally capped at ``max_pages``."""
        page = self
        seen = 0
        while True:
            yield page
            seen += 1
            if max_pages is not None and seen >= max_pages:
                return
            if not page.has_next_page():
                return
            page = await page._fetch_next()

    async def get_next_page(self) -> Self | None:
        """Fetch the next page, or ``None`` if this is the last one."""
        if not self.has_next_page():
            return None
        return await self._fetch_next()

    async def _fetch_next(self) -> Self:
        return cast(
            "Self",
            await self._client._request(
                self._method,
                self._path,
                body=self._next_body(),
                cast_to=type(self),
                timeout=self._timeout,
            ),
        )


class AsyncCursorPage(AsyncPaginator[ItemT], Generic[ItemT]):
    """Cursor-paginated page (``search.people`` / ``search.companies``)."""

    total_results: int | None = None
    results_length: int | None = None
    max_results: int | None = None
    cursor: str | None = None

    def has_next_page(self) -> bool:
        # The API terminates the walk by returning ``cursor=null`` on the last page, so a
        # non-null cursor is the single source of truth. We deliberately do NOT also gate
        # on ``results`` being non-empty: a sparse intermediate page (empty results but a
        # valid forward cursor) must keep paging, not silently truncate the result set.
        return bool(self.cursor)

    def _next_body(self) -> dict[str, Any]:
        # Guard against a non-advancing cursor: if the API hands back the same cursor it was
        # given, paging again would re-fetch (and re-bill) the same page forever. ``_body``
        # holds the cursor that fetched THIS page (bound after the request), so a cheap equality
        # check breaks the loop instead of spinning. Mirrors the JS SDK's CursorPage guard.
        if self.cursor is not None and self.cursor == self._body.get("cursor"):
            raise BlitzError(
                "Cursor did not advance: the API returned the same cursor it was given. "
                "Aborting to avoid an infinite pagination loop."
            )
        return {**self._body, "cursor": self.cursor}


class AsyncPageNumberPage(AsyncPaginator[ItemT], Generic[ItemT]):
    """Page-number-paginated page (``search.employee_finder``)."""

    company_linkedin_url: str | None = None
    max_results: int | None = None
    results_length: int | None = None
    page: int | None = None
    total_pages: int | None = None

    def _current_page(self) -> int:
        # Prefer the page the server echoed; fall back to the page we requested
        # (default 1) so iteration still advances even if the field is absent.
        if self.page is not None:
            return self.page
        requested = self._body.get("page")
        return requested if isinstance(requested, int) else 1

    def has_next_page(self) -> bool:
        return (
            self.total_pages is not None
            and self._current_page() < self.total_pages
            and bool(self.results)
        )

    def _next_body(self) -> dict[str, Any]:
        return {**self._body, "page": self._current_page() + 1}
