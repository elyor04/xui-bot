"""Exceptions raised by the 3x-ui API client."""
from __future__ import annotations


class XUIError(Exception):
    """Base error for any 3x-ui API failure."""


class XUIAuthError(XUIError):
    """Authentication failed or the session/token is no longer valid."""


class XUIRequestError(XUIError):
    """The panel returned ``success=false`` or a non-2xx HTTP status."""

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status
