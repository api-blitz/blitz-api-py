"""Response models for the Feedback resource."""

from __future__ import annotations

from ._models import BlitzModel

__all__ = [
    "FeedbackResponse",
]


class FeedbackResponse(BlitzModel):
    """Result of ``feedback.send``: a confirmation that the feedback was recorded.

    It carries no ticket id and no reply. It subclasses :class:`BlitzModel`, not
    ``BlitzResponse``: the spec's ``200`` schema for ``/v2/feedback`` lists only
    ``success`` and ``message``, with no ``fair_usage`` block.
    """

    #: ``True`` when the feedback was recorded.
    success: bool | None = None
    #: Confirmation text, such as ``"Thanks, your feedback has been sent to the Blitz team."``
    message: str | None = None
