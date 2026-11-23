"""The Feedback resource: ``client.feedback``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._compat import TimeoutParam
from ...types.feedback import FeedbackResponse

if TYPE_CHECKING:
    from ..._client import AsyncBlitzAPI

_FEEDBACK = "/v2/feedback"


class AsyncFeedbackResource:
    def __init__(self, client: AsyncBlitzAPI) -> None:
        self._client = client

    async def send(
        self,
        *,
        subject: str,
        message: str,
        contact: str,
        timeout: TimeoutParam = None,
    ) -> FeedbackResponse:
        """Send a bug report, a feature request, or any other feedback to the Blitz team.

        It can be about the API, data quality, the docs, or the MCP server. Costs 0 records,
        and every API key can call it, whatever endpoints the key has access to. Returns a
        confirmation that the feedback was recorded; there is no ticket id and no reply.

        Args:
            subject: One-line summary of the feedback, 1 to 200 characters.
            message: The feedback itself, as free text, 1 to 4,000 characters: what went
                wrong, what is missing, or what worked well. When it is about a request,
                include the endpoint, the request id from ``fair_usage.request_id``, and
                what you expected.
            contact: Email address where the Blitz team can reach the person who gives the
                feedback, up to 200 characters. Ask that person for it; do not guess it.
        """
        return await self._client._request(
            "POST",
            _FEEDBACK,
            body={"subject": subject, "message": message, "contact": contact},
            cast_to=FeedbackResponse,
            timeout=timeout,
        )
